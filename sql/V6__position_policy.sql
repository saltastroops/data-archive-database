SET search_path TO observations;

-- Policy for hiding target coordinates of proprietary observations from users who don't own the observation data.

ALTER TABLE position ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS position_policy ON position;

CREATE POLICY position_policy ON position
USING (
    current_setting('my.institution_user_id')::int = ANY(position.owner_institution_user_ids)
    OR position.owner_institution_user_ids IS NULL
);