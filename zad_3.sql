"UPDATE TableName SET TableField = TableField + 1 WHERE SomeFilterField = @ParameterID"

create table users(
user_id int primary key,
name varchar2(255),
password varchar2(255),
last_login date,
last_failed_login date,
failed_attemps_login int,
block_after int
);

create table fake_users(
fake_user_id int primary key,
name varchar2(255),
last_failed_login date,
failed_attemps_login int,
block_after int
);

create sequence user2_id MINVALUE 1 START with 1;
create sequence fake_user_id MINVALUE 1 START with 1;