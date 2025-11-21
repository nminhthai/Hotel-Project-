-- Bước 1: Tạo người dùng và các vai trò
	-- Tạo login trên server
	CREATE LOGIN AdminUser WITH PASSWORD = '123'
	CREATE LOGIN DEUser WITH PASSWORD = '456'
	CREATE LOGIN DAUser WITH PASSWORD = '789'

	-- Tạo người dùng liên kết với Login
	USE [Booking]
	CREATE USER admin_user1 FOR LOGIN  AdminUser
	CREATE USER de_user2 FOR LOGIN  DEUser
	CREATE USER da_user3 FOR LOGIN  DAUser

-- Bước 2: Phân quyền cho từng người dùng
	-- Cấp toàn quyền cho admin_user1
	ALTER ROLE db_owner ADD MEMBER admin_user1

	-- Cấp quyền đọc, ghi dữ liệu, quản lý schema và các lệnh DDL cho de_user2 
	ALTER ROLE db_datareader ADD MEMBER de_user2
	ALTER ROLE db_datawriter ADD MEMBER de_user2
	ALTER ROLE db_ddladmin ADD MEMBER de_user2
	GRANT EXECUTE ON SCHEMA::dbo TO de_user2

	-- Cấp quyền đọc dữ liệu cho da_user3
	ALTER ROLE db_datareader ADD MEMBER da_user3

-- Bước 3: Xác minh và kiểm tra phân quyền 
SELECT 
    princ.name AS PrincipalName,
    perm.permission_name AS PermissionName,
    perm.state_desc AS PermissionState,
    CASE 
        WHEN perm.major_id = 0 THEN 'Database Level' 
        ELSE 'Schema/Object Level'
    END AS Scope
FROM 
    sys.database_permissions AS perm
JOIN 
    sys.database_principals AS princ ON perm.grantee_principal_id = princ.principal_id
WHERE 
    princ.name IN ('admin_user1', 'de_user2', 'da_user3')  
ORDER BY 
    PrincipalName, Scope;


