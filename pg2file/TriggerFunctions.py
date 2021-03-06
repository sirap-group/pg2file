from sqlalchemy.sql.expression import text
from sqlalchemy.engine import create_engine
import os
from pg2file.SqlStrings import PG_CONN_STR

SQL_TRIGGER_FUNCTIONS = """
SELECT r.specific_schema as "schema", 
    regexp_replace(r.routine_name || '(' 
        || replace(coalesce((select string_agg(format_type(argtypeid,-1), ',') from (select unnest(p.proargtypes) as argtypeid ) as args), ''), '"', '''')
        || ')', '[\?:\/\\\]', '_', 'g')  as "function_name",
    pg_get_functiondef(p.oid) as "function_def"
FROM information_schema.routines r
    left join pg_proc p on (p.proname=r.routine_name)
WHERE r.specific_schema NOT IN ('pg_catalog', 'information_schema') and r.type_udt_name = 'trigger'
ORDER BY r.specific_schema, r.routine_name
"""

def GetTriggerFunctions(host, database, user, password):
    try:
        connection_string = PG_CONN_STR.format(hostName=host, dbName=database, userName=user, password=password )
        conn = create_engine(connection_string, client_encoding='utf8').engine.connect()
        functions = conn.execute(text(SQL_TRIGGER_FUNCTIONS)).fetchall()
        return functions
    except Exception:
        raise
    finally:
        conn.close()
        

def WriteTriggerFunctions(path, host, db, user, password):
    functions = GetTriggerFunctions(host=host,
                                    database=db,
                                    user=user,
                                    password=password)
    for function in functions:
        path_out = os.path.join(path,  function[0], 'trigger_functions', function[1] + '.sql')
        if not os.path.exists(os.path.dirname(path_out)):
            os.makedirs(os.path.dirname(path_out))
        print path_out
        f = open(path_out, 'w')
        try:
            f.write(function[2])
        finally:
            f.close()