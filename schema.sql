-- CREATE DATABASE IF NOT EXISTS garment_db;
-- USE garment_db;

CREATE TABLE IF NOT EXISTS production_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_no VARCHAR(50),
    buyer_name VARCHAR(100),
    style_no VARCHAR(50),
    order_quantity INT,
    production_date DATE,
    day_target INT,
    day_achieved INT,
    hour_1 INT,
    hour_2 INT,
    hour_3 INT,
    hour_4 INT,
    hour_5 INT,
    hour_6 INT,
    hour_7 INT,
    hour_8 INT,
    fabric_type VARCHAR(50),
    fabric_gsm INT,
    color VARCHAR(50),
    planned_fabric_meters DECIMAL(10,2),
    actual_fabric_used DECIMAL(10,2),
    rejection INT,
    rework INT,
    planned_cut_quantity INT,
    actual_cut_quantity INT,
    operator_code VARCHAR(50),
    line_no INT
);

-- Indexes for optimization
CREATE INDEX idx_date ON production_data(production_date);
CREATE INDEX idx_buyer ON production_data(buyer_name);
CREATE INDEX idx_line ON production_data(line_no);
CREATE INDEX idx_style ON production_data(style_no);
