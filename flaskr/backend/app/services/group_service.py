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
            letters = ''.join(random.choices(string.ascii_uppercase, k=4))
            numbers = ''.join(random.choices(string.digits, k=4))
            code = f"{letters}{numbers}"
            
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
            if league not in ["Premier League", "La Liga", "UEFA Champions League"]:
                return None, "Invalid league selected"

            if tracked_team_ids:
                existing_teams = Team.query.filter(Team.id.in_(tracked_team_ids)).all()
                if len(existing_teams) != len(tracked_team_ids):
                    return None, "One or more selected teams are invalid"

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
            db.session.flush()

            member = GroupMember(
                group_id=group.id,
                user_id=creator_id,
                role=MemberRole.ADMIN,
                joined_at=datetime.now(timezone.utc)
            )
            db.session.add(member)

            if tracked_team_ids:
                for team_id in tracked_team_ids:
                    tracker = TeamTracker(
                        group_id=group.id,
                        team_id=team_id,
                        added_at=datetime.now(timezone.utc)
                    )
                    db.session.add(tracker)

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
    def is_group_admin(user_id: int, group_id: int) -> bool:
        """Check if user is admin of the group"""
        member = GroupMember.query.filter_by(
            group_id=group_id,
            user_id=user_id
        ).first()
        return member and member.role == MemberRole.ADMIN

    @staticmethod
    def update_member_role(group_id: int, user_id: int, new_role: MemberRole) -> Tuple[bool, str]:
        """Update a member's role in the group"""
        try:
            member = GroupMember.query.filter_by(
                group_id=group_id,
                user_id=user_id
            ).first()

            if not member:
                return False, "Member not found"

            if member.role == MemberRole.ADMIN:
                return False, "Cannot modify admin role"

            audit_log = GroupAuditLog(
                group_id=group_id,
                user_id=user_id,
                action="ROLE_UPDATED",
                details={"new_role": new_role.value},
                created_at=datetime.now(timezone.utc)
            )
            db.session.add(audit_log)

            member.role = new_role
            member.last_active = datetime.now(timezone.utc)
            db.session.commit()

            return True, f"Role updated to {new_role.value}"

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating member role: {str(e)}")
            return False, "Failed to update role"

    @staticmethod
    def join_group(invite_code: str, user_id: int) -> Tuple[bool, str]:
        """Process a group join request."""
        try:
            group = Group.query.filter_by(invite_code=invite_code).first()
            if not group:
                return False, "Invalid invite code"

            existing_member = GroupMember.query.filter_by(
                group_id=group.id,
                user_id=user_id
            ).first()
            if existing_member:
                return False, "Already a member of this group"

            pending = PendingMembership.query.filter_by(
                group_id=group.id,
                user_id=user_id,
                status=MembershipStatus.PENDING
            ).first()
            if pending:
                return False, "Join request already pending"

            if group.privacy_type == GroupPrivacyType.SEMI_PRIVATE:
                pending = PendingMembership(
                    group_id=group.id,
                    user_id=user_id,
                    requested_at=datetime.now(timezone.utc)
                )
                db.session.add(pending)
                message = "Join request sent to group admin"
            else:
                member = GroupMember(
                    group_id=group.id,
                    user_id=user_id,
                    role=MemberRole.MEMBER,
                    joined_at=datetime.now(timezone.utc),
                    last_active=datetime.now(timezone.utc)
                )
                db.session.add(member)
                message = "Successfully joined group"

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
            existing_teams = Team.query.filter(Team.id.in_(team_ids)).all()
            if len(existing_teams) != len(team_ids):
                return False, "One or more selected teams are invalid"

            TeamTracker.query.filter_by(group_id=group_id).delete()

            for team_id in team_ids:
                tracker = TeamTracker(
                    group_id=group_id,
                    team_id=team_id,
                    added_at=datetime.now(timezone.utc)
                )
                db.session.add(tracker)

            audit_log = GroupAuditLog(
                group_id=group_id,
                action="UPDATE_TRACKED_TEAMS",
                details={"team_ids": team_ids},
                created_at=datetime.now(timezone.utc)
            )
            db.session.add(audit_log)

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

            audit_log = GroupAuditLog(
                group_id=group_id,
                user_id=user_id,
                action="MEMBER_REMOVED",
                created_at=datetime.now(timezone.utc)
            )
            db.session.add(audit_log)

            db.session.delete(member)
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

    @staticmethod
    def get_audit_logs(group_id: int, page: int = 1, per_page: int = 20) -> List[Dict]:
        """Get audit logs for a group with pagination"""
        try:
            logs = GroupAuditLog.query.filter_by(group_id=group_id)\
                .order_by(GroupAuditLog.created_at.desc())\
                .paginate(page=page, per_page=per_page, error_out=False)
                
            return [{
                'id': log.id,
                'action': log.action,
                'user': log.user.username,
                'details': log.details,
                'created_at': log.created_at.isoformat()
            } for log in logs.items]
        except Exception as e:
            current_app.logger.error(f"Error getting audit logs: {str(e)}")
            return []

    @staticmethod
    def get_member_activity(group_id: int) -> List[Dict]:
        """Get member activity statistics"""
        try:
            members = GroupMember.query.filter_by(group_id=group_id).all()
            return [{
                'user_id': member.user_id,
                'username': member.user.username,
                'joined_at': member.joined_at.isoformat(),
                'last_active': member.last_active.isoformat() if member.last_active else None,
                'total_predictions': len(member.user.predictions),
                'total_points': sum(p.points for p in member.user.predictions if p.points)
            } for member in members]
        except Exception as e:
            current_app.logger.error(f"Error getting member activity: {str(e)}")
            return []