SET search_path TO observations, extensions;

-- policy for hiding target coordinates of proprietary observations to not belonging members

ALTER TABLE observations.position ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS position_policy ON observations.position;

CREATE POLICY position_policy ON observations.position
USING (
    current_setting('my.institution_user_id')::int = ANY(observations.position.institution_member_user_ids)
    OR observations.position.institution_member_user_ids IS NULL
);