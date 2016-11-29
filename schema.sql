CREATE TABLE stocked_item (
	id INTEGER PRIMARY KEY,
	name TEXT,
	description TEXT,
	count INT
);

CREATE TABLE listings (
	listing_id INT PRIMARY KEY,
	title TEXT,
	url TEXT
);

CREATE TABLE product_variation (
	listing_id INT,
	variation_name TEXT,
	variation_value TEXT,
	variation_id INT,
	PRIMARY KEY (listing_id, variation_id)
);

CREATE TABLE variation_to_stock (
	listing_id INT,
	variation_id INT,
	stock_id INT,
	count INT
);

CREATE TABLE transactions (
	transaction_id INTEGER PRIMARY KEY,
	listing_id INT,
	size_id INT,
	dt INT
);