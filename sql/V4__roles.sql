-- Editing observation data

CREATE ROLE observations_editor;

GRANT USAGE ON SCHEMA observations, admin, extensions TO observations_editor;
GRANT SELECT, USAGE ON ALL SEQUENCES IN SCHEMA observations TO observations_editor;

GRANT SELECT ON ALL TABLES IN SCHEMA observations TO observations_editor;

GRANT DELETE, INSERT ON TABLE admin.proposal_investigator TO observations_editor;
GRANT DELETE, INSERT ON TABLE observations.artifact TO observations_editor;
GRANT DELETE, INSERT ON TABLE observations.energy TO observations_editor;
GRANT DELETE, INSERT ON TABLE observations.hrs_setup TO observations_editor;
GRANT DELETE, INSERT ON TABLE observations.instrument_keyword_value TO observations_editor;
GRANT DELETE, INSERT ON TABLE observations.instrument_setup TO observations_editor;
GRANT DELETE, INSERT ON TABLE observations.observation TO observations_editor;
GRANT DELETE, INSERT ON TABLE observations.observation_group TO observations_editor;
GRANT DELETE, INSERT ON TABLE observations.observation_time TO observations_editor;
GRANT DELETE, INSERT ON TABLE observations.plane TO observations_editor;
GRANT DELETE, INSERT ON TABLE observations.polarization TO observations_editor;
GRANT DELETE, INSERT ON TABLE observations.position TO observations_editor;
GRANT DELETE, INSERT ON TABLE observations.proposal TO observations_editor;
GRANT DELETE, INSERT ON TABLE observations.rss_setup TO observations_editor;
GRANT DELETE, INSERT ON TABLE observations.target TO observations_editor;

-- Editing admin data

CREATE ROLE admin_editor;

GRANT USAGE ON SCHEMA observations, admin, extensions TO admin_editor;
GRANT SELECT, USAGE ON ALL SEQUENCES IN SCHEMA admin TO admin_editor;
GRANT SELECT, USAGE ON ALL SEQUENCES IN SCHEMA observations TO admin_editor;

GRANT SELECT ON ALL TABLES IN SCHEMA admin TO admin_editor;
GRANT SELECT ON ALL TABLES IN SCHEMA observations TO admin_editor;

GRANT INSERT, UPDATE ON TABLE admin.data_request TO admin_editor;
GRANT INSERT ON TABLE admin.data_request_artifact TO admin_editor;
GRANT INSERT, UPDATE ON TABLE admin.ssda_user TO admin_editor;
GRANT INSERT, UPDATE ON TABLE admin.ssda_user_auth TO admin_editor;
