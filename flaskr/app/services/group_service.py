import string
import random
import qrcode
import io
from typing import List, Optional, Dict, Tuple
from datetime import datetime, timezone
from flask import current_app
from sqlalchemy.exc import IntegrityError

from app.models import (
    Group, Users, GroupMember, TeamTracker, PendingMembership, GroupAuditLog,
    GroupPrivacyType, MemberRole, MembershipStatus
)
from app.db import db

class GroupService:
    @staticmethod
    def generate_invite_code() -> str:
        """Generate a unique 8-character invite code."""
        while True:
            # Generate code: 4 letters and 4 numbers without hyphen
            letters = ''.join(random.choices(string.ascii_uppercase, k=4))
            numbers = ''.join(random.choices(string.digits, k=4))
            code = f"{letters}{numbers}"  # 8 chars total (4 letters + 4 numbers)
            
            # Check if code already exists
            if not Group.query.filter_by(invite_code=code).first():
                return code

    @staticmethod
    def get_group_members(group_id: int) -> List[Dict]:
        """Get all members of a group with their roles"""
        try:
            members = (GroupMember.query
                      .join(Users, Users.id == GroupMember.user_id)
                      .filter(GroupMember.group_id == group_id)
                      .order_by(GroupMember.role.desc(), Users.username)
                      .all())
            
            return [{
                'user_id': member.user_id,
                'username': member.user.username,
                'role': member.role,
                'joined_at': member.joined_at,
                'last_active': member.last_active
            } for member in members]
        except Exception as e:
            current_app.logger.error(f"Error getting group members: {str(e)}")
            return []

    @staticmethod
    def get_pending_requests(group_id: int) -> List[Dict]:
        """Get all pending join requests for a group"""
        try:
            requests = (PendingMembership.query
                       .join(Users, Users.id == PendingMembership.user_id)
                       .filter(
                           PendingMembership.group_id == group_id,
                           PendingMembership.status == MembershipStatus.PENDING
                       )
                       .order_by(PendingMembership.requested_at)
                       .all())
            
            return [{
                'request_id': req.id,
                'user_id': req.user_id,
                'username': req.user.username,
                'requested_at': req.requested_at
            } for req in requests]
        except Exception as e:
            current_app.logger.error(f"Error getting pending requests: {str(e)}")
            return []

    @staticmethod
    def create_group(
        name: str,
        league: str,
        creator_id: int,
        privacy_type: GroupPrivacyType = GroupPrivacyType.PRIVATE,
        description: Optional[str] = None,
        tracked_team_ids: Optional[List[int]] = None
    ) -> Tuple[Group, str]:
        """
        Create a new group and set up initial structure.
        Returns tuple of (group, error_message)
        """
        try:
            # Create group
            group = Group(
                name=name,
                league=league,
                creator_id=creator_id,
                invite_code=GroupService.generate_invite_code(),
                privacy_type=privacy_type,
                description=description
            )
            db.session.add(group)
            db.session.flush()  # Get group ID without committing

            # Add creator as admin
            member = GroupMember(
                group_id=group.id,
                user_id=creator_id,
                role=MemberRole.ADMIN
            )
            db.session.add(member)

            # Add tracked teams
            if tracked_team_ids:
                for team_id in tracked_team_ids:
                    tracker = TeamTracker(
                        group_id=group.id,
                        team_id=team_id
                    )
                    db.session.add(tracker)

            # Log creation
            audit_log = GroupAuditLog(
                group_id=group.id,
                user_id=creator_id,
                action="CREATE_GROUP",
                details={
                    "name": name,
                    "league": league,
                    "privacy_type": privacy_type.value
                }
            )
            db.session.add(audit_log)

            db.session.commit()
            return group, None

        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating group: {str(e)}")
            return None, "A group with this name already exists"
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating group: {str(e)}")
            return None, "An error occurred while creating the group"

    @staticmethod
    def join_group(invite_code: str, user_id: int) -> Tuple[bool, str]:
        """
        Process a group join request.
        Returns tuple of (success, message)
        """
        try:
            group = Group.query.filter_by(invite_code=invite_code).first()
            if not group:
                return False, "Invalid invite code"

            # Check if user is already a member
            existing_member = GroupMember.query.filter_by(
                group_id=group.id,
                user_id=user_id
            ).first()
            if existing_member:
                return False, "Already a member of this group"

            # Check for pending request
            pending = PendingMembership.query.filter_by(
                group_id=group.id,
                user_id=user_id,
                status=MembershipStatus.PENDING
            ).first()
            if pending:
                return False, "Join request already pending"

            if group.privacy_type == GroupPrivacyType.SEMI_PRIVATE:
                # Create pending membership
                pending = PendingMembership(
                    group_id=group.id,
                    user_id=user_id
                )
                db.session.add(pending)
                message = "Join request sent to group admin"
            else:
                # Direct join for private groups
                member = GroupMember(
                    group_id=group.id,
                    user_id=user_id,
                    role=MemberRole.MEMBER
                )
                db.session.add(member)
                message = "Successfully joined group"

            # Log join attempt
            audit_log = GroupAuditLog(
                group_id=group.id,
                user_id=user_id,
                action="JOIN_REQUEST",
                details={
                    "status": "PENDING" if group.privacy_type == GroupPrivacyType.SEMI_PRIVATE else "APPROVED"
                }
            )
            db.session.add(audit_log)

            db.session.commit()
            return True, message

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error joining group: {str(e)}")
            return False, "An error occurred while processing your request"

    @staticmethod
    def process_join_request(
        request_id: int,
        admin_id: int,
        approved: bool
    ) -> Tuple[bool, str]:
        """Process a pending join request."""
        try:
            request = PendingMembership.query.get(request_id)
            if not request:
                return False, "Invalid request"

            # Verify admin has permission
            admin_member = GroupMember.query.filter_by(
                group_id=request.group_id,
                user_id=admin_id,
                role=MemberRole.ADMIN
            ).first()
            if not admin_member:
                return False, "Unauthorized"

            if approved:
                # Create group membership
                member = GroupMember(
                    group_id=request.group_id,
                    user_id=request.user_id,
                    role=MemberRole.MEMBER
                )
                db.session.add(member)
                request.status = MembershipStatus.APPROVED
                message = "Request approved"
            else:
                request.status = MembershipStatus.REJECTED
                message = "Request rejected"

            request.processed_at = datetime.now(timezone.utc)
            request.processed_by = admin_id

            # Log action
            audit_log = GroupAuditLog(
                group_id=request.group_id,
                user_id=admin_id,
                action="PROCESS_JOIN_REQUEST",
                details={
                    "request_id": request_id,
                    "user_id": request.user_id,
                    "status": "APPROVED" if approved else "REJECTED"
                }
            )
            db.session.add(audit_log)

            db.session.commit()
            return True, message

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error processing join request: {str(e)}")
            return False, "An error occurred while processing the request"

    @staticmethod
    def generate_qr_code(invite_code: str) -> bytes:
        """Generate QR code for invite link."""
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(invite_code)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            return img_buffer.getvalue()

        except Exception as e:
            current_app.logger.error(f"Error generating QR code: {str(e)}")
            return None

    @staticmethod
    def bulk_member_action(
        group_id: int,
        admin_id: int,
        user_ids: List[int],
        action: str
    ) -> Tuple[bool, str, Dict]:
        """
        Perform bulk actions on group members.
        Actions: REMOVE, PROMOTE_MODERATOR, REMOVE_MODERATOR
        Returns: (success, message, results)
        """
        try:
            # Verify admin permissions
            admin_member = GroupMember.query.filter_by(
                group_id=group_id,
                user_id=admin_id,
                role=MemberRole.ADMIN
            ).first()
            if not admin_member:
                return False, "Unauthorized", {}

            results = {"successful": [], "failed": []}
            
            for user_id in user_ids:
                try:
                    member = GroupMember.query.filter_by(
                        group_id=group_id,
                        user_id=user_id
                    ).first()
                    
                    if not member:
                        results["failed"].append({"user_id": user_id, "reason": "Not a member"})
                        continue

                    if action == "REMOVE":
                        if member.role == MemberRole.ADMIN:
                            results["failed"].append({"user_id": user_id, "reason": "Cannot remove admin"})
                            continue
                        db.session.delete(member)
                        
                    elif action == "PROMOTE_MODERATOR":
                        if member.role != MemberRole.MEMBER:
                            results["failed"].append({"user_id": user_id, "reason": "Invalid role change"})
                            continue
                        member.role = MemberRole.MODERATOR
                        
                    elif action == "REMOVE_MODERATOR":
                        if member.role != MemberRole.MODERATOR:
                            results["failed"].append({"user_id": user_id, "reason": "Not a moderator"})
                            continue
                        member.role = MemberRole.MEMBER

                    results["successful"].append(user_id)
                    
                    # Log action
                    audit_log = GroupAuditLog(
                        group_id=group_id,
                        user_id=admin_id,
                        action=f"BULK_{action}",
                        details={
                            "target_user_id": user_id,
                            "status": "SUCCESS"
                        }
                    )
                    db.session.add(audit_log)

                except Exception as e:
                    results["failed"].append({"user_id": user_id, "reason": str(e)})

            db.session.commit()
            
            success = len(results["successful"]) > 0
            message = f"Processed {len(results['successful'])} members successfully"
            if results["failed"]:
                message += f", {len(results['failed'])} failed"
                
            return success, message, results

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error in bulk member action: {str(e)}")
            return False, "An error occurred during the operation", {"successful": [], "failed": user_ids}

    @staticmethod
    def regenerate_invite_code(group_id: int) -> Optional[str]:
        """Regenerate invite code for a group"""
        try:
            group = Group.query.get(group_id)
            if not group:
                return None

            new_code = GroupService.generate_invite_code()
            group.invite_code = new_code
            db.session.commit()
            return new_code
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error regenerating invite code: {str(e)}")
            return None