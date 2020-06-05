SET search_path TO observations, extensions;

-- "Unknown" data product type

INSERT INTO data_product_type (product_type)
VALUES ('Unknown');

-- "Unknown" instrument mode

INSERT INTO instrument_mode (instrument_mode)
VALUES ('Unknown');

-- "Unknown" intent

INSERT INTO intent (intent)
VALUES ('Unknown');

-- "Unknown" detector mode

INSERT INTO detector_mode (detector_mode)
VALUES ('Unknown');

-- "Unknown" product category

INSERT INTO product_category (product_category_id, product_category)
VALUES (7, 'Unknown');

-- "Unknown" product type

WITH product_category_id (id) AS (
    SELECT product_category_id FROM product_category WHERE product_category.product_category='Unknown'
)
INSERT INTO product_type (product_category_id, product_type)
VALUES((SELECT id FROM product_category_id), 'Unknown');
