"""Undo / redo history of recorded editing actions."""


class EditHistory:
    """Stores edit actions and the current position within them."""

    MAX_SIZE = 50

    def __init__(self):
        self.actions = []
        self.current_step = 0

    def clear(self):
        """Forget every recorded action."""
        self.actions = []
        self.current_step = 0

    def active_actions(self):
        """Return the actions that are currently applied."""
        return self.actions[:self.current_step]

    def can_undo(self):
        return self.current_step > 0

    def can_redo(self):
        return self.current_step < len(self.actions)

    def push(self, entry):
        """
        Record a new action, discarding any redo steps.

        If the history grows past MAX_SIZE, the oldest action is dropped and
        returned so the caller can bake it into the base image. Returns None
        when nothing was dropped.
        """
        self.actions = self.actions[:self.current_step]
        self.actions.append(entry)
        self.current_step += 1

        if len(self.actions) > self.MAX_SIZE:
            oldest = self.actions.pop(0)
            self.current_step -= 1
            return oldest

        return None

    def undo(self):
        """Step back. Returns True if the position changed."""
        if self.can_undo():
            self.current_step -= 1
            return True
        return False

    def redo(self):
        """Step forward. Returns True if the position changed."""
        if self.can_redo():
            self.current_step += 1
            return True
        return False
