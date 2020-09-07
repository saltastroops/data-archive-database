SET search_path TO admin;

DROP TABLE data_request_status;

ALTER TABLE  data_request DROP COLUMN path, data_request_status_id;


