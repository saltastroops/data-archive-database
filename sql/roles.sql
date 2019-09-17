-- Editing observation data

CREATE ROLE observations_editor;

GRANT USAGE ON SCHEMA observations, admin, extensions TO observations_editor;
GRANT SELECT, USAGE ON ALL SEQUENCES IN SCHEMA observations TO observations_editor;

GRANT SELECT ON ALL TABLES IN SCHEMA observations TO observations_editor;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA observations TO observations_editor;

GRANT DELETE, INSERT ON TABLE admin.proposal_investigator TO observations_editor;
GRANT DELETE, INSERT ON TABLE observations.artifact TO observations_editor;
GRANT DELETE, INSERT ON TABLE observations.energy TO observations_editor;
GRANT DELETE, INSERT ON TABLE observations.instrument_keyword_value TO observations_editor;
GRANT DELETE, INSERT ON TABLE observations.observation TO observations_editor;
GRANT DELETE, INSERT ON TABLE observations.observation_time TO observations_editor;
GRANT DELETE, INSERT ON TABLE observations.plane TO observations_editor;
GRANT DELETE, INSERT ON TABLE observations.polarization TO observations_editor;
GRANT DELETE, INSERT ON TABLE observations.position TO observations_editor;
GRANT DELETE, INSERT ON TABLE observations.proposal TO observations_editor;
GRANT DELETE, INSERT ON TABLE observations.target TO observations_editor;

CREATE ROLE admin_editor;
