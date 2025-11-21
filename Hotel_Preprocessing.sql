CREATE PROCEDURE CleanAndTransformHotelData
AS
BEGIN
    -- 1. Chuyển đổi cột Giá thành INT, loại bỏ các ký tự không phải số.
    UPDATE Hotel_cleaned_copy
    SET Price = TRY_CAST(REPLACE(REPLACE(REPLACE(Price, CHAR(160), ''), 'VND', ''), '.', '') AS INT);

    -- 2. Chuyển đổi cột Điểm thành FLOAT.
    UPDATE Hotel_cleaned_copy
    SET Score = TRY_CAST(REPLACE(SUBSTRING(CONVERT(VARCHAR(50), Score), CHARINDEX(CHAR(10), Score) + 1, LEN(Score)), ',', '.') AS FLOAT);

    -- 3. Chuyển đổi cột Số lượng đánh giá thành INT.
    UPDATE Hotel_cleaned_copy
    SET ReviewsCount = 
        CASE 
            WHEN CHARINDEX(' ', ReviewsCount) > 0 
                THEN TRY_CAST(REPLACE(SUBSTRING(CONVERT(VARCHAR(50), ReviewsCount), 1, CHARINDEX(' ', ReviewsCount) - 1), '.', '') AS INT)
            WHEN ISNUMERIC(ReviewsCount) = 1
                THEN TRY_CAST(REPLACE(ReviewsCount, '.', '') AS INT) 
        END;

    -- 4. Chuyển đổi các cột đánh giá thành FLOAT.
    UPDATE Hotel_cleaned_copy
    SET 
        Facilities = TRY_CAST(REPLACE(Facilities, ',', '.') AS FLOAT),
        Comfort = TRY_CAST(REPLACE(Comfort, ',', '.') AS FLOAT),
        Staff = TRY_CAST(REPLACE(Staff, ',', '.') AS FLOAT),
        FreeWifi = TRY_CAST(REPLACE(FreeWifi, ',', '.') AS FLOAT),
        ValueForMoney = TRY_CAST(REPLACE(ValueForMoney, ',', '.') AS FLOAT),
        Cleanliness = TRY_CAST(REPLACE(Cleanliness, ',', '.') AS FLOAT),
        Location = TRY_CAST(REPLACE(Location, ',', '.') AS FLOAT);

    -- 5. Xóa các bản ghi trùng lặp.
    DELETE FROM Hotel_cleaned_copy
    WHERE HotelID NOT IN (
        SELECT MIN(HotelID)
        FROM Hotel_cleaned_copy
        GROUP BY HotelName, Price, Score, City
    );

    -- 6. Xóa các bản ghi nếu tất cả các cột điểm đánh giá đều NULL hoặc rỗng.
    DELETE FROM Hotel_cleaned_copy
    WHERE (Score IS NULL OR Score = '')
      AND (Facilities IS NULL OR Facilities = '')
      AND (Comfort IS NULL OR Comfort = '')
      AND (Staff IS NULL OR Staff = '')
      AND (FreeWifi IS NULL OR FreeWifi = '')
      AND (ValueForMoney IS NULL OR ValueForMoney = '')
      AND (Cleanliness IS NULL OR Cleanliness = '')
      AND (Location IS NULL OR Location = '');

    -- 7. Cập nhật các giá trị điểm đánh giá trống bằng giá trị Điểm chính.
    UPDATE Hotel_cleaned_copy
    SET Facilities = CASE WHEN Facilities = '' THEN Score ELSE Facilities END,
        Comfort = CASE WHEN Comfort = '' THEN Score ELSE Comfort END,
        Staff = CASE WHEN Staff = '' THEN Score ELSE Staff END,
        FreeWifi = CASE WHEN FreeWifi = '' THEN Score ELSE FreeWifi END,
        ValueForMoney = CASE WHEN ValueForMoney = '' THEN Score ELSE ValueForMoney END,
        Cleanliness = CASE WHEN Cleanliness = '' THEN Score ELSE Cleanliness END,
        Location = CASE WHEN Location = '' THEN Score ELSE Location END
    WHERE Facilities = ''
       OR Comfort = ''
       OR Staff = ''
       OR FreeWifi = ''
       OR ValueForMoney = ''
       OR Cleanliness = ''
       OR Location = '';

    -- 8. Chèn các thành phố duy nhất vào bảng City.
    INSERT INTO City (City)
    SELECT DISTINCT City
    FROM Hotel_cleaned_copy
    WHERE NOT EXISTS (
        SELECT 1 FROM City WHERE City.City = Hotel_cleaned_copy.City
    );

	-- 9. Chèn dữ liệu khách sạn vào bảng Hotel.
    INSERT INTO Hotel (HotelID, HotelName, Price, CityID)
    SELECT DISTINCT HotelID, HotelName, Price,
           (SELECT CityID FROM City WHERE City = Hotel_cleaned_copy.City)
    FROM Hotel_cleaned_copy;

    -- 10. Chèn dữ liệu đánh giá vào bảng Review.
    INSERT INTO Review (Score, ReviewsCount, AvgReview, Facilities, Comfort, Staff, FreeWifi, ValueForMoney, Cleanliness, Location, HotelID, ScrapeDate)
    SELECT Score, ReviewsCount, AvgReview, Facilities, Comfort, Staff, FreeWifi, ValueForMoney, Cleanliness, Location, HotelID, ScrapeDate
    FROM Hotel_cleaned_copy;

END;


EXEC CleanAndTransformHotelData
DROP PROC CleanAndTransformHotelData

SELECT * FROM City;  -- Kiểm tra bảng City
SELECT * FROM Review;  -- Kiểm tra bảng Review
SELECT * FROM Hotel;  -- Kiểm tra bảng Hotel

