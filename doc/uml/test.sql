CREATE TABLE "system"."users" (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    active BOOLEAN
);

CREATE TABLE "user"."tablea" (
    order_id INT,
    user_id INT,
    amount DECIMAL(10,2)
);

CREATE TABLE "user"."tableb" (
    order_id INT,
    user_id INT,
    amount DECIMAL(10,2)
);