from __future__ import annotations

from app.models.schemas import ActionType, Action


REQUIRES_APPROVAL = {
    ActionType.form_submit,
    ActionType.login,
    ActionType.send_mail,
    ActionType.delete_file,
    ActionType.purchase,
    ActionType.system_change,
}


class PolicyEngine:
    def needs_approval(self, action: Action) -> bool:
        return action.type in REQUIRES_APPROVAL
