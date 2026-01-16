import logging
import re

logger = logging.getLogger(__name__)

# Pattern for validating SQL identifiers (table names, column names)
# Allows alphanumeric characters, underscores, and common prefixes like dbo.
_VALID_IDENTIFIER_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)?$')


def _validate_identifier(identifier: str, identifier_type: str = "identifier") -> str:
    """Validate that a SQL identifier (table name, etc.) is safe.

    Args:
        identifier: The identifier to validate.
        identifier_type: Description of the identifier type for error messages.

    Returns:
        The validated identifier.

    Raises:
        ValueError: If the identifier contains invalid characters.
    """
    if not identifier:
        raise ValueError(f"SQL {identifier_type} cannot be empty")
    if not _VALID_IDENTIFIER_PATTERN.match(identifier):
        raise ValueError(
            f"Invalid SQL {identifier_type}: '{identifier}'. "
            f"Identifiers must start with a letter or underscore and contain only "
            f"alphanumeric characters, underscores, and optionally a schema prefix (e.g., 'dbo.tablename')."
        )
    return identifier


class DbConnect:
    """DbConnect is a wrapper for either a pyodbc or sqlite3 connection. It can then be
    passed into the DbReader and DbWriter classes to retrieve/store document data.
    """

    def __init__(
        self, driver=None, server=None, db=None, user=None, pwd=None, conn=None
    ):
        """Create a new DbConnect object. You can pass in either information for a pyodbc connection string
        or directly pass in a sqlite or pyodbc connection object.

        If conn is None, all other arguments must be supplied. If conn is passed in, all other arguments will be ignored.

        Args:
            driver
            server
            db:
            user
            pwd
            conn
        """
        if conn is None:
            if not all([driver, server, db, user, pwd]):
                raise ValueError(
                    "If you are not passing in a connection object, "
                    "you must pass in all other arguments to create a DB connection."
                )
            import pyodbc

            self.conn = pyodbc.connect(
                "DRIVER={0};SERVER={1};DATABASE={2};USER={3};PWD={4}".format(
                    driver, server, db, user, pwd
                )
            )
        else:
            self.conn = conn
        self.cursor = self.conn.cursor()
        # according this thread, bulk insert for sqlserver need to set fast_executemany=True.
        # https://stackoverflow.com/questions/29638136/how-to-speed-up-bulk-insert-to-ms-sql-server-using-pyodbc
        if hasattr(self.cursor, 'fast_executemany'):
            self.cursor.fast_executemany = True

        import sqlite3

        if isinstance(self.conn, sqlite3.Connection):
            self.db_lib = "sqlite3"
            self.database_exception = sqlite3.DatabaseError
        else:
            import pyodbc
            if isinstance(self.conn, pyodbc.Connection):
                self.db_lib = "pyodbc"
                self.database_exception = pyodbc.DatabaseError
            else:
                raise ValueError(
                    "conn must be either a sqlite3 or pyodbc Connection object, not {0}".format(
                        type(self.conn)
                    )
                )

        logger.info("Opened connection to %s.%s", server, db)

    def create_table(self, query, table_name, drop_existing):
        # Validate table_name to prevent SQL injection
        _validate_identifier(table_name, "table name")

        if drop_existing:
            try:
                self.cursor.execute(f"drop table if exists {table_name}")
            except self.database_exception:
                pass
            else:
                self.conn.commit()
        try:
            self.cursor.execute(query)
        except self.database_exception as e:
            self.conn.rollback()
            self.conn.close()
            raise e
        else:
            self.conn.commit()
            logger.info("Created table %s with query: %s", table_name, query)

    def write(self, query, data):
        try:
            self.cursor.executemany(query, data)
        except self.database_exception as e:
            self.conn.rollback()
            self.conn.close()
            raise e
        else:
            self.conn.commit()
            # print("Wrote {0} rows with query: {1}".format(len(data), query))

    def read(self, query):
        self.cursor.execute(query)
        result = self.cursor.fetchall()
        # print("Read {0} rows with query: {1}".format(len(result), query))
        return result

    def close(self):
        self.conn.commit()
        self.conn.close()
        logger.info("Connection closed.")
