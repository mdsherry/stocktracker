CREATE TABLE stocked_item (
	id PRIMARY KEY,
	name TEXT,
	description TEXT
);

CREATE TABLE listings (
	listing_id INT,
	title TEXT,
	url TEXT
);

CREATE TABLE product_variation (
	listing_id INT,
	variation_name TEXT,
	variation_value TEXT,
	variation_id INT
);

CREATE TABLE variation_to_stock (
	listing_id INT,
	variation_id INT,
	stock_id INT,
	count INT
);

-- CREATE TABLE transactions (
-- 	id PRIMARY KEY,
-- 	receipt_id INT,
-- 	listing_id INT,
-- 	dt,


-- )