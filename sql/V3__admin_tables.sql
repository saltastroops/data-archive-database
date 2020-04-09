DROP SCHEMA IF EXISTS admin CASCADE;

CREATE SCHEMA admin;

SET search_path TO admin, observations;

-- LOOKUP TABLES

-- access_rule

DROP TABLE IF EXISTS access_rule;

CREATE TABLE access_rule(
    access_rule_id  serial PRIMARY KEY,
    access_rule     varchar(32) NOT NULL
);

COMMENT ON TABLE access_rule IS 'Rules for data access.'

INSERT INTO access_rule (access_rule)
values  ('PUBLIC_OR_INSTITUTION_MEMBER'),
        ('PUBLIC_OR_OWNER');

-- auth_provider

DROP TABLE IF EXISTS auth_provider;

CREATE TABLE auth_provider
(
    auth_provider_id serial PRIMARY KEY,
    auth_provider    varchar(32) UNIQUE NOT NULL,
    description      varchar(255)       NOT NULL
);

COMMENT ON TABLE auth_provider IS 'Authentication providers.';

INSERT INTO auth_provider (auth_provider, description)
VALUES ('SSDA', 'SAAO/SALT Data Archive'),
       ('SDB', 'SALT Science Database');

-- calibration_level

DROP TABLE IF EXISTS calibration_level;

CREATE TABLE calibration_level
(
    calibration_level_id serial PRIMARY KEY,
    calibration_level    varchar(32) UNIQUE NOT NULL
);

COMMENT ON TABLE calibration_level IS 'Calibration levels.';

INSERT INTO calibration_level (calibration_level)
VALUES ('Raw'),
       ('Reduced');

-- calibration_type

DROP TABLE IF EXISTS calibration_type;

CREATE TABLE calibration_type
(
    calibration_type_id serial PRIMARY KEY,
    calibration_type    varchar(32) UNIQUE NOT NULL
);

COMMENT ON TABLE calibration_type IS 'Calibration types.';

INSERT INTO calibration_type (calibration_type)
VALUES ('Arc'),
       ('Bias'),
       ('Flat'),
       ('Radial Velocity Standard'),
       ('Spectrophotometric Standard');

-- data_request_status

DROP TABLE IF EXISTS data_request_status;

CREATE TABLE data_request_status
(
    data_request_status_id bigserial PRIMARY KEY,
    status                 varchar(45) UNIQUE NOT NULL
);

COMMENT ON TABLE data_request_status IS 'Status of a data request, such as pending or successful.';

INSERT INTO data_request_status (status)
VALUES ('Expired'),
       ('Failed'),
       ('Pending'),
       ('Successful');

-- role

DROP TABLE IF EXISTS role;

CREATE TABLE role (
    role_id serial PRIMARY KEY,
    role varchar(30) UNIQUE NOT NULL
);

COMMENT ON TABLE role IS 'User role for permissions.';

INSERT INTO role (role)
VALUES ('Administrator');

-- OTHER TABLES

-- ssda_session

DROP TABLE IF EXISTS ssda_session;

CREATE TABLE "ssda_session" (
  "sid" varchar NOT NULL COLLATE "default",
  "sess" json NOT NULL,
  "expire" timestamp(6) NOT NULL
)
WITH (OIDS=FALSE);

ALTER TABLE "ssda_session" ADD CONSTRAINT "session_pkey" PRIMARY KEY ("sid") NOT DEFERRABLE INITIALLY IMMEDIATE;

COMMENT ON TABLE ssda_session IS 'A session cookie for the Data Archive.';
-- See https://github.com/voxpelli/node-connect-pg-simple/blob/master/table.sql

-- ssda_user

DROP TABLE IF EXISTS ssda_user;

CREATE TABLE ssda_user (
  ssda_user_id serial PRIMARY KEY,
  affiliation varchar(255) NOT NULL,
  auth_provider_id int NOT NULL REFERENCES auth_provider (auth_provider_id),
  auth_provider_user_id varchar(50) NOT NULL,
  email varchar(255) NOT NULL,
  family_name varchar(255) NOT NULL,
  given_name varchar(255) NOT NULL
);

CREATE INDEX ssda_user_auth_provider_idx ON ssda_user (auth_provider_id);
CREATE UNIQUE INDEX ssda_user_auth_provider_user_unique ON ssda_user (auth_provider_id, auth_provider_user_id);

COMMENT ON TABLE ssda_user IS 'A data archive user.';
COMMENT ON COLUMN ssda_user.affiliation IS 'Institution (such as a university) to which the user is affiliated.';
COMMENT ON COLUMN ssda_user.auth_provider_id IS 'Authentication provider used for validating the user''s credentials.';
COMMENT ON COLUMN ssda_user.auth_provider_user_id IS 'Unique id the authentication uses for identifying the user.';
COMMENT ON COLUMN ssda_user.family_name IS 'Family name (surname) of the user.';
COMMENT ON COLUMN ssda_user.given_name IS 'Given name (first name) of the user.';

-- ssda_user_auth

DROP TABLE IF EXISTS ssda_user_auth;

CREATE TABLE ssda_user_auth (
    password varchar(255) NOT NULL,
    password_reset_token varchar(255) UNIQUE,
    password_reset_token_expiry timestamp with time zone,
    user_id int NOT NULL REFERENCES ssda_user (ssda_user_id) ON DELETE CASCADE,
    username varchar(255) UNIQUE NOT NULL
);

CREATE INDEX ssda_user_auth_user_idx ON ssda_user_auth (user_id);
CREATE INDEX ssda_user_auth_username_idx ON ssda_user_auth (username);

COMMENT ON TABLE ssda_user_auth IS 'Authentication details for a data archive user.';
COMMENT ON COLUMN ssda_user_auth.password IS 'Securely hashed password of the user.';
COMMENT ON COLUMN ssda_user_auth.password_reset_token IS 'Token which can be used to reset the password.';
COMMENT ON COLUMN ssda_user_auth.password_reset_token_expiry IS 'Date and time when the password reset token expires.';
COMMENT ON COLUMN ssda_user_auth.username IS 'Username of the user.';

-- user_role

DROP TABLE IF EXISTS user_role;

CREATE TABLE user_role (
                           role_id int NOT NULL REFERENCES role (role_id),
    user_id int NOT NULL REFERENCES ssda_user (ssda_user_id)
);

CREATE INDEX user_role_role_idx ON user_role (role_id);
CREATE INDEX user_role_user_idx ON user_role (user_id);

COMMENT ON TABLE user_role IS 'Join table between users and user roles.';

-- data_request

DROP TABLE IF EXISTS data_request;

CREATE TABLE data_request
(
    data_request_id        bigserial PRIMARY KEY,
    data_request_status_id int                      NOT NULL REFERENCES data_request_status (data_request_status_id),
    made_at                timestamp with time zone NOT NULL,
    path                   varchar(200),
    ssda_user_id           int                      NOT NULL REFERENCES ssda_user (ssda_user_id)
);

CREATE INDEX data_request_status_fk ON data_request (data_request_status_id);
CREATE INDEX data_request_user_fk ON data_request (ssda_user_id);

COMMENT ON TABLE data_request IS 'Request for a set of data files.';
COMMENT ON COLUMN data_request.made_at IS 'Date and time when the request was made.';
COMMENT ON COLUMN data_request.ssda_user_id IS 'User who made the request.';
COMMENT ON COLUMN data_request.path IS 'Path to the file containing the requested data.';

-- data_request_artifact

DROP TABLE IF EXISTS data_request_artifact;

CREATE TABLE data_request_artifact
(
    data_request_id int REFERENCES data_request (data_request_id),
    artifact_id     int REFERENCES observations.artifact (artifact_id)
);

CREATE INDEX data_request_artifact_artifact_fk ON data_request_artifact (artifact_id);
CREATE INDEX data_request_artifact_data_request_fk ON data_request_artifact (data_request_id);

COMMENT ON TABLE data_request_artifact IS 'Join table between data requests and artifacts.';

-- data_request_calibration_level

DROP TABLE IF EXISTS data_request_calibration_level;

CREATE TABLE data_request_calibration_level
(
    data_request_id          int REFERENCES data_request (data_request_id),
    calibration_level_id     int REFERENCES calibration_level (calibration_level_id)
);

CREATE INDEX data_request_calibration_level_calibration_level_fk ON data_request_calibration_level (calibration_level_id);
CREATE INDEX data_request_calibration_level_data_request_fk ON data_request_calibration_level (data_request_id);
CREATE UNIQUE INDEX data_request_calibration_level_data_request_unique ON data_request_calibration_level (calibration_level_id, data_request_id);

COMMENT ON TABLE data_request_calibration_level IS 'Join table between data requests and the calibration levels.';

-- data_request_calibration_type

DROP TABLE IF EXISTS data_request_calibration_type;

CREATE TABLE data_request_calibration_type
(
    data_request_id          int REFERENCES data_request (data_request_id),
    calibration_type_id      int REFERENCES calibration_type (calibration_type_id)
);

CREATE INDEX data_request_calibration_type_calibration_type_fk ON data_request_calibration_type (calibration_type_id);
CREATE INDEX data_request_calibration_type_data_request_fk ON data_request_calibration_type (data_request_id);
CREATE UNIQUE INDEX data_request_calibration_type_data_request_unique ON data_request_calibration_type (calibration_type_id, data_request_id);

COMMENT ON TABLE data_request_calibration_type IS 'Join table between data requests and the calibration types.';

-- institution_user

DROP TABLE IF EXISTS institution_user;

CREATE TABLE institution_user (
    institution_id      int NOT NULL REFERENCES observations.institution (institution_id),
    institution_member  boolean NOT NULL,
    institution_user_id varchar(50) NOT NULL,
    ssda_user_id        int NOT NULL REFERENCES ssda_user (ssda_user_id)
);

CREATE INDEX institution_user_institution_idx ON institution_user (institution_id);
CREATE INDEX institution_user_institution_user_idx ON institution_user (institution_user_id);
CREATE INDEX institution_user_ssda_user ON institution_user (ssda_user_id);

COMMENT ON TABLE institution_user IS 'Table for linking a data archive user to a user account at an institution such as SALT.';
COMMENT ON COLUMN institution_user.institution_user_id IS 'Id used by the institution to identify the user. This must be consistent with the id used in the proposal_investigator table.';

-- proposal_access_rule

DROP TABLE IF EXISTS proposal_access_rule;

CREATE TABLE proposal_access_rule (
    proposal_id      int NOT NULL REFERENCES observations.proposal (proposal_id),
    access_rule_id   int NOT NULL REFERENCES access_rule (access_rule_id)
);

CREATE INDEX proposal_access_rule_proposal_idx ON proposal_access_rule(proposal_id);
CREATE INDEX proposal_access_rule.access_rule_idx ON proposal_access_rule(access_rule_id);

COMMENT ON TABLE proposal_access IS 'Join table between proposals and access rules'.

-- proposal_investigator

DROP TABLE IF EXISTS proposal_investigator;

CREATE TABLE proposal_investigator (
    institution_user_id varchar(50) NOT NULL,
    proposal_id int NOT NULL REFERENCES observations.proposal (proposal_id) ON DELETE CASCADE
);

CREATE INDEX proposal_investigator_user_idx ON proposal_investigator (institution_user_id);
CREATE INDEX proposal_investigator_proposal_idx ON proposal_investigator (proposal_id);

COMMENT ON TABLE proposal_investigator IS 'Investigator on a proposal.';
COMMENT ON COLUMN proposal_investigator.institution_user_id IS 'Id used to identify the investigator by the institution to which the proposal was submitted.';


