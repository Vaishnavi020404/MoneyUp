-- -- -- SQLite 
select * from stock_prices ;


-- -- latest stock prices for Apple

-- -- select * from stock_prices where symbol='AAPL' order by datetime desc limit 5;

-- -- average price of all the stocks
-- -- select symbol, AVG(close) as average_price from stock_prices group by symbol;

-- -- stock with highest price

-- select symbol,max(high) as max_price from stock_prices group by symbol order by max_price desc limit 1;


-- -- stock with lowest price
-- select symbol,min(low) as min_price from stock_prices group by symbol order by min_price asc limit 1;

-- -- stock with highest average price
-- select symbol, AVG(close) as average_price from stock_prices group by symbol order by average_price desc limit 1;

-- -- stock with total trading volume
-- select symbol, SUM(volume) as total_volume from stock_prices group by symbol order by total_volume;

-- -- latest market price for all stocks
-- select symbol,close from stock_prices where datetime=(select max(datetime) from stock_prices);


