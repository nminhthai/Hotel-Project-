-- SAO LƯU FULL BACKUP LẦN ĐẦU TIÊN CHO CƠ SỞ DỮ LIỆU
CREATE PROCEDURE sp_BackupFullDatabase
AS
BEGIN
    DECLARE @BackupFileName NVARCHAR(255);
    
    -- Tạo tên tệp sao lưu với ngày và giờ
    SET @BackupFileName = N'C:\Backups\Backup\Booking_FullBackup_' + 
                          FORMAT(GETDATE(), 'yyyyMMdd_HHmmss') + '.bak';

    -- Sao lưu Full Backup cơ sở dữ liệu
    BACKUP DATABASE [Booking]
    TO DISK = @BackupFileName
    WITH INIT, NAME = 'Full Backup of Booking'; -- INIT: chỉ ghi đè 1 lần

END;
GO

-- SAO LƯU DIFFERENTAIL BACKUP CHO CƠ SỞ DỮ LIỆU
CREATE PROCEDURE sp_BackupDifferentialDatabase
AS
BEGIN
    DECLARE @BackupFileName NVARCHAR(255);
    
    -- Tạo tên tệp sao lưu với ngày và giờ
    SET @BackupFileName = N'C:\Backups\Backup\Booking_DifferentialBackup_' + 
                          FORMAT(GETDATE(), 'yyyyMMdd_HHmmss') + '.bak';

    -- Sao lưu Differential Backup cơ sở dữ liệu
    BACKUP DATABASE [Booking]
    TO DISK = @BackupFileName
    WITH 
        DIFFERENTIAL, 
        NAME = N'Differential Backup of Booking';
END;
GO

-- LÊN LỊCH SAO LƯU FULL BACKUP HÀNG TUẦN
CREATE PROCEDURE sp_ScheduleWeeklyFullBackup
AS
BEGIN
        -- Tạo công việc sao lưu Full Backup hàng tuần
        EXEC msdb.dbo.sp_add_job
            @job_name = N'Weekly Full Backup Job',
            @enabled = 1;

        -- Tạo bước công việc sao lưu Full Backup
        EXEC msdb.dbo.sp_add_jobstep
            @job_name = 'Weekly Full Backup Job',
            @step_name = 'Step1',
            @subsystem = 'TSQL',
            @command = 'EXEC sp_BackupFullDatabase;',
            @database_name = 'master',
            @on_success_action = 1,
            @on_fail_action = 2;

        -- Lên lịch hàng tuần (00:00 AM Chủ Nhật)
        EXEC msdb.dbo.sp_add_schedule
            @schedule_name = N'Weekly Full Backup Schedule',
            @enabled = 1,
            @freq_type = 8,                 -- Lịch hàng tuần
            @freq_interval = 1,             -- Chạy mỗi tuần
            @freq_recurrence_factor = 1,    -- Chạy mỗi tuần
            @active_start_time = 000000;    -- Thời gian: 00:00 AM

        -- Gắn lịch vào công việc
        EXEC msdb.dbo.sp_attach_schedule
            @job_name = N'Weekly Full Backup Job',
            @schedule_name = N'Weekly Backup Schedule';

        -- Kích hoạt công việc
        EXEC msdb.dbo.sp_add_jobserver
            @job_name = N'Weekly Full Backup Job',
            @server_name = N'LAPTOP-GE6HN70J\SQLSERVER';
END;
GO

-- LÊN LỊCH SAO LƯU DIFFERENTIAL BACKUP HÀNG NGÀY
CREATE PROCEDURE sp_ScheduleDailyDifferentialBackup
AS
BEGIN
        -- Tạo công việc sao lưu Differential Backup hàng ngày
        EXEC msdb.dbo.sp_add_job
            @job_name = N'Daily Differential Backup Job',
            @enabled = 1;

        -- Tạo bước công việc sao lưu Differential Backup
        EXEC msdb.dbo.sp_add_jobstep
            @job_name = 'Daily Differential Backup Job',
            @step_name = 'Step2',
            @subsystem = 'TSQL',
            @command = 'EXEC sp_BackupDifferentialDatabase;',
            @database_name = 'master',
            @on_success_action = 1,
            @on_fail_action = 2;

        -- Lên lịch hàng ngày (00:00 AM)
        EXEC msdb.dbo.sp_add_schedule
            @schedule_name = N'Daily Differential Backup Schedule',
            @enabled = 1,
            @freq_type = 4,                 -- Lịch hàng ngày
            @freq_interval = 1,             -- Mỗi ngày
            @active_start_time = 000000;    -- Thời gian: 00:00 AM

        -- Gắn lịch vào công việc
        EXEC msdb.dbo.sp_attach_schedule
            @job_name = N'Daily Differential Backup Job',
            @schedule_name = N'Daily Differential Backup Schedule';

        -- Kích hoạt công việc
        EXEC msdb.dbo.sp_add_jobserver
            @job_name = N'Daily Differential Backup Job',
            @server_name = N'LAPTOP-GE6HN70J\SQLSERVER';
END;
GO

-- QUẢN LÝ SAO LƯU
-- Xóa các sao lưu cũ
CREATE PROCEDURE sp_DeleteOldBackups
AS
BEGIN
    DECLARE @DeleteBeforeDate DATETIME;
    
    -- Đặt thời gian xóa các sao lưu cũ hơn 6 tháng
    SET @DeleteBeforeDate = DATEADD(MONTH, -6, GETDATE());
    
    -- Xóa các tệp sao lưu Full Backup cũ
    EXEC xp_delete_file 0, N'C:\Backups\Backup\', N'bak', @DeleteBeforeDate;

    -- Xóa các tệp sao lưu Differential Backup cũ
    EXEC xp_delete_file 0, N'C:\Backups\Backup\', N'bak', @DeleteBeforeDate;
    
    PRINT N'Đã xóa thành công bản sao lưu cũ';
END;
GO

-- Thông báo khi có lỗi trong quá trình sao lưu
CREATE PROCEDURE sp_ManageBackupAlerts
AS
BEGIN
    -- Tạo một Operator để nhận thông báo qua email
    EXEC msdb.dbo.sp_add_operator
        @name = N'BackupErrorOperator',
        @enabled = 1,
        @email_address = N'nhathong16112004@gmail.com';

    -- Tạo Alert để nhận thông báo khi có lỗi trong sao lưu
    EXEC msdb.dbo.sp_add_alert
        @name = N'Backup Failure Alert',
        @message_id = 3205,               -- Mã lỗi liên quan đến việc sao lưu thất bại
        @severity = 16,                   -- Mức độ nghiêm trọng của lỗi
        @notification_message = N'Sao lưu cơ sở dữ liệu Booking không thành công',
        @job_id = NULL;                   -- Cảnh báo khi có sự cố xảy ra trong công việc sao lưu

    -- Liên kết Alert với Operator để gửi email
    EXEC msdb.dbo.sp_add_notification
        @alert_name = N'Backup Failure Alert',
        @operator_name = N'BackupErrorOperator',
        @notification_method = 1;  -- 1 = Email
END;

-- Ghi lại nhật ký sao lưu vào một bảng
CREATE PROCEDURE sp_LogBackupHistory
AS
CREATE TABLE BackupHistory (
    BackupFileName NVARCHAR(255),
    BackupDate DATETIME
);

BEGIN
    DECLARE @BackupFileName NVARCHAR(255);
    DECLARE @BackupDate DATETIME;
    
    -- Lấy tên tệp sao lưu và ngày sao lưu
    SET @BackupFileName = (SELECT TOP 1 bmf.physical_device_name
                           FROM msdb.dbo.backupset bs
                           INNER JOIN msdb.dbo.backupmediafamily bmf 
                               ON bs.media_set_id = bmf.media_set_id
                           WHERE bs.database_name = 'Booking'
                           AND bs.type = 'D'
                           ORDER BY bs.backup_finish_date DESC);
    
    SET @BackupDate = GETDATE();
    
    -- Lưu thông tin sao lưu vào bảng lịch sử sao lưu
    INSERT INTO BackupHistory (BackupFileName, BackupDate)
    VALUES (@BackupFileName, @BackupDate);
    
    PRINT N'Lịch sử sao lưu đã được ghi lại thành công';
END;
GO

