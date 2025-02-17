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
    GroupPrivacyType, MemberRole, MembershipStatus, Team
)
from app.db import db

class GroupService:
    VALID_LEAGUES = {
        "PL": "Premier League",
        "LL": "La Liga",
        "UCL": "UEFA Champions League"
    }

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
    ) -> Tuple[Optional[Group], Optional[str]]:
        """Create a new group with tracking details."""
        try:
            # Validate league format
            if league not in ["Premier League", "La Liga", "UEFA Champions League"]:
                return None, "Invalid league selected"

            # Validate tracked teams exist
            if tracked_team_ids:
                existing_teams = Team.query.filter(Team.id.in_(tracked_team_ids)).all()
                if len(existing_teams) != len(tracked_team_ids):
                    return None, "One or more selected teams are invalid"

            # Create group
            group = Group(
                name=name,
                league=league,
                creator_id=creator_id,
                invite_code=GroupService.generate_invite_code(),
                privacy_type=privacy_type,
                description=description,
                created=datetime.now(timezone.utc)
            )
            db.session.add(group)
            db.session.flush()  # Get group ID

            # Add creator as admin
            member = GroupMember(
                group_id=group.id,
                user_id=creator_id,
                role=MemberRole.ADMIN,
                joined_at=datetime.now(timezone.utc)
            )
            db.session.add(member)

            # Add tracked teams
            if tracked_team_ids:
                for team_id in tracked_team_ids:
                    tracker = TeamTracker(
                        group_id=group.id,
                        team_id=team_id,
                        added_at=datetime.now(timezone.utc)
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
                    "tracked_teams": tracked_team_ids,
                    "privacy_type": privacy_type.value
                },
                created_at=datetime.now(timezone.utc)
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
        """Process a group join request."""
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
                    user_id=user_id,
                    requested_at=datetime.now(timezone.utc)
                )
                db.session.add(pending)
                message = "Join request sent to group admin"
            else:
                # Direct join for private groups
                member = GroupMember(
                    group_id=group.id,
                    user_id=user_id,
                    role=MemberRole.MEMBER,
                    joined_at=datetime.now(timezone.utc),
                    last_active=datetime.now(timezone.utc)
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
                },
                created_at=datetime.now(timezone.utc)
            )
            db.session.add(audit_log)

            db.session.commit()
            return True, message

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error joining group: {str(e)}")
            return False, "An error occurred while processing your request"

    @staticmethod
    def update_tracked_teams(group_id: int, team_ids: List[int]) -> Tuple[bool, Optional[str]]:
        """Update tracked teams for a group."""
        try:
            # Validate teams exist
            existing_teams = Team.query.filter(Team.id.in_(team_ids)).all()
            if len(existing_teams) != len(team_ids):
                return False, "One or more selected teams are invalid"

            # Clear existing tracked teams
            TeamTracker.query.filter_by(group_id=group_id).delete()

            # Add new tracked teams
            for team_id in team_ids:
                tracker = TeamTracker(
                    group_id=group_id,
                    team_id=team_id,
                    added_at=datetime.now(timezone.utc)
                )
                db.session.add(tracker)

            db.session.commit()
            return True, None
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating tracked teams: {str(e)}")
            return False, "Failed to update tracked teams"

    @staticmethod
    def get_tracked_teams(group_id: int) -> List[int]:
        """Get list of tracked team IDs for a group."""
        try:
            trackers = TeamTracker.query.filter_by(group_id=group_id).all()
            return [tracker.team_id for tracker in trackers]
        except Exception as e:
            current_app.logger.error(f"Error getting tracked teams: {str(e)}")
            return []

    @staticmethod
    def remove_member(group_id: int, user_id: int) -> Tuple[bool, str]:
        """Remove a member from the group."""
        try:
            member = GroupMember.query.filter_by(
                group_id=group_id,
                user_id=user_id
            ).first()

            if not member:
                return False, "Member not found"

            if member.role == MemberRole.ADMIN:
                return False, "Cannot remove admin"

            db.session.delete(member)

            # Log removal
            audit_log = GroupAuditLog(
                group_id=group_id,
                user_id=user_id,
                action="MEMBER_REMOVED",
                created_at=datetime.now(timezone.utc)
            )
            db.session.add(audit_log)

            db.session.commit()
            return True, "Member removed successfully"

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error removing member: {str(e)}")
            return False, "Failed to remove member"

    @staticmethod
    def regenerate_invite_code(group_id: int) -> Optional[str]:
        """Regenerate invite code for a group."""
        try:
            group = Group.query.get(group_id)
            if not group:
                return None

            new_code = GroupService.generate_invite_code()
            group.invite_code = new_code

            # Log regeneration
            audit_log = GroupAuditLog(
                group_id=group_id,
                user_id=group.creator_id,
                action="REGENERATE_INVITE_CODE",
                created_at=datetime.now(timezone.utc)
            )
            db.session.add(audit_log)

            db.session.commit()
            return new_code
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error regenerating invite code: {str(e)}")
            return None

    @staticmethod
    def generate_qr_code(invite_code: str) -> Optional[bytes]:
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