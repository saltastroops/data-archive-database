SET search_path TO admin;

ALTER TABLE  data_request DROP COLUMN path, DROP COLUMN data_request_status_id;

DROP INDEX data_request_status_fk ON data_request;

DROP TABLE data_request_status;


