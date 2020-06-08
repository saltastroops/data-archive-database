SET search_path TO admin, observations, extensions;

-- Trigger function for when an insert in the institution user table is executed

CREATE OR REPLACE FUNCTION update_proposal_investigator() RETURNS trigger AS
$BODY$
    BEGIN
        UPDATE proposal_investigator
        SET proposal_investigator.institution_member_user_id = NEW.institution_member_user_id
        FROM observations.proposal
        WHERE proposal_investigator.proposal_id=proposal.proposal_id
            AND proposal_investigator.institution_user_id = NEW.institution_user_id;

        RETURN NEW;
    END;
$BODY$ LANGUAGE plpgsql;

-- An insert trigger on the institution user table
CREATE TRIGGER create_institution_user
AFTER INSERT
ON institution_user
FOR EACH ROW
EXECUTE PROCEDURE update_proposal_investigator();
