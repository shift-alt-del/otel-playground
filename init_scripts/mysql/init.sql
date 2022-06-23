GRANT ALL PRIVILEGES ON *.* TO 'example-user' WITH GRANT OPTION;
ALTER USER 'example-user'@'%' IDENTIFIED WITH mysql_native_password BY 'example-pw';
FLUSH PRIVILEGES;

create table T_PV_COUNT(URL varchar(64) not null primary key);