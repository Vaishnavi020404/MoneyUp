-- -- 1 Average price per stock
-- SELECT 
--     symbol,
--     ROUND(AVG(close),2) AS avg_price
-- FROM stock_prices
-- GROUP BY symbol
-- ORDER BY avg_price DESC;


-- -- 2 Latest price of each stock
-- SELECT 
--     symbol,
--     close,
--     fetched_at
-- FROM stock_prices
-- WHERE fetched_at IN (
--     SELECT MAX(fetched_at)
--     FROM stock_prices
--     GROUP BY symbol
-- );


-- -- 3 Highest price recorded per stock
-- SELECT
--     symbol,
--     MAX(high) AS highest_price
-- FROM stock_prices
-- GROUP BY symbol
-- ORDER BY highest_price DESC;


-- -- 4 Lowest price recorded per stock
-- SELECT
--     symbol,
--     MIN(low) AS lowest_price
-- FROM stock_prices
-- GROUP BY symbol
-- ORDER BY lowest_price;


-- -- 5 Stock volatility (price range)
-- SELECT
--     symbol,
--     ROUND(MAX(high) - MIN(low),2) AS volatility
-- FROM stock_prices
-- GROUP BY symbol
-- ORDER BY volatility DESC;


-- -- 6 Total number of records collected
-- SELECT COUNT(*) AS total_records
-- FROM stock_prices;


-- -- 7 Number of records per stock
-- SELECT
--     symbol,
--     COUNT(*) AS records
-- FROM stock_prices
-- GROUP BY symbol
-- ORDER BY records DESC;