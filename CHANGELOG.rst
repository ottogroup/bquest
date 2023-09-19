Development
***********

0.4.0 (2023-09-19)
******************

- fix version 0.3.2 by adding default case for sql_with_substitutions

0.3.2 (2023-09-19)
******************

- Add condition for string substitution so that empty substitutions together with sqls,
  that contain curly brackets won't fail

0.3.1 (2023-08-15)
******************

- Manually bump pandas-gbq version

0.3.0 (2023-08-15)
******************

- Raise pandas to 2.0

0.2.1 (2023-08-09)
******************

- Add test coverage report
- Make consistent use of original_table_id/test_table_id
- Add tests for is_sql

0.2.0 (2023-06-12)
******************

- Remove redundant project_id in BQConfigRunner and SQLRunner

0.1.0 (2023-06-12)
******************

- Lower pandas requirement to 1.5.0

0.0.1 (2023-06-09)
******************

- Initial release
