create table users (
    login varchar(30) primary key,
    name text,
    last_name text,
    email text,
    password varchar(50),
    sha_password varchar(50),
    note text);

create table projects (
    id varchar(30) primary key,
    admin varchar(30),
    create_date date,
    due_date date,
    brief varchar(50),
    description text,
    active boolean,
    foreign key (admin) references users(login));

create table user_project (
    user varchar(30),
    project varchar(30),
    foreign key (user) references users(login),
    foreign key (project) references projects(id));

create table project_requests (
    user varchar(30),
    project varchar(30),
    foreign key (user) references users(login),
    foreign key (project) references projects(id));

create table tags (
    project varchar(30),
    tag varchar(30),
    foreign key (project) references projects(id),
    primary key (project, tag));

create table services (
    project varchar(30),
    type varchar(30),
    subtype varchar(30),
    name varchar(30),
    field varchar(30),
    value text,
    foreign key (project) references projects(id),
    primary key (project, type, subtype, name, field));

