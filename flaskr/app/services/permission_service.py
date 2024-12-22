from typing import Optional
from flask import current_app
from app.models import GroupMember, MemberRole

class PermissionService:
    @staticmethod
    def check_group_permission(user_id: int, group_id: int, required_role: MemberRole) -> bool:
        """Check if user has required role in group."""
        try:
            member = GroupMember.query.filter_by(
                user_id=user_id,
                group_id=group_id
            ).first()

            if not member:
                return False

            # Admin can do everything
            if member.role == MemberRole.ADMIN:
                return True

            # Moderator can do moderator and member things
            if member.role == MemberRole.MODERATOR and required_role != MemberRole.ADMIN:
                return True

            # Member can only do member things
            return member.role == required_role

        except Exception as e:
            current_app.logger.error(f"Permission check error: {str(e)}")
            return False