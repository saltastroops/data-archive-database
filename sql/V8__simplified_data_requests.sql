SET search_path TO admin;

DROP INDEX data_request_status_fk;

ALTER TABLE  data_request DROP COLUMN path, DROP COLUMN data_request_status_id;

DROP TABLE data_request_status;


