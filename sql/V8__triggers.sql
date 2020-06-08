SET search_path TO admin, observations, extensions;

-- Trigger function for when an insert in the institution user table is executed

CREATE OR REPLACE FUNCTION update_proposal_investigator() RETURNS trigger AS
$BODY$
    BEGIN
        UPDATE admin.proposal_investigator pi
        SET pi.institution_member_user_id = NEW.institution_member_user_id
        FROM observations.proposal p
        WHERE pi.proposal_id=p.proposal_id AND pi.institution_user_id = NEW.institution_user_id;

        RETURN NEW;
    END;
$BODY$ LANGUAGE plpgsql;

-- An insert trigger
CREATE TRIGGER create_institution_user
AFTER INSERT
ON admin.institution_user
FOR EACH ROW
EXECUTE PROCEDURE update_proposal_investigator();
