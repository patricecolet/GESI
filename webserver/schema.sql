
drop table if exists entries;
create table entries (
  id integer primary key autoincrement,
  title text not null,
  filename text not null,
  env text not null,
  density text not null,
  blacklist text not null
);

