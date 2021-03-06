from jsonMode import createDatabase, createTable, dropDatabase, alterAddPK
from parse.ast_node import ASTNode
from parse.symbol_table import SymbolTable, TableSymbol, FieldSymbol, TypeSymbol, SymbolType
from parse.errors import Error, ErrorType


class CreateEnum(ASTNode):
    def __init__(self, name, value_list, line, column, graph_ref):
        ASTNode.__init__(self, line, column)
        self.name = name.upper()  # type name
        self.value_list = value_list  # list of possible values
        self.graph_ref = graph_ref

    def execute(self, table: SymbolTable, tree):
        super().execute(table, tree)
        result_values = []
        for val in self.value_list:          
            result_values.append(val.execute(table, tree))
        symbol = TypeSymbol(self.name, result_values)
        table.add(symbol)
        print(f'[AST] ENUM {self.name} created.')
        return f'[AST] ENUM {self.name} created.'


class CreateDatabase(ASTNode):
    def __init__(self, name, owner, mode, replace, exists, line, column, graph_ref):
        ASTNode.__init__(self, line, column)
        self.name = name  # database name
        self.owner = owner  # optional owner
        self.mode = mode  # mode integer
        self.replace = replace  # boolean type
        self.exists = exists
        self.graph_ref=graph_ref

    def execute(self, table: SymbolTable, tree):
        super().execute(table, tree)
        #result_name = self.name.execute(table, tree)
        #result_owner = self.owner.execute(table, tree) if self.owner else None  # Owner seems to be stored only to ST
        #result_mode = self.owner.mode(table, tree) if self.mode else 6  # Change to 1 when default mode from EDD available
        result_name = self.name.execute(table, tree)
        result_owner = self.owner
        result_mode = self.mode
        result = 0
        if self.replace:
            dropDatabase(result_name)
        
        #if result_mode == 6:  # add more ifs when modes from EDD available
        result = createDatabase(result_name)

        if result == 1:
            # log error on operation
            raise Error(0, 0, ErrorType.RUNTIME, '5800: system_error')
            return False
        elif result == 2 and self.exists == False:
            # log error because db already exists
            raise Error(0, 0, ErrorType.RUNTIME, '42P04: duplicate_database')
            return False
        else:            
            #return table.add(DatabaseSymbol(result_name, result_owner, result_mode)) #chaged by loadDatabases
            table.LoadDataBases()
            return ['Database \'' + result_name + '\' was created successfully!']

class CreateTable(ASTNode):  # TODO: Check grammar, complex instructions are not added yet
    def __init__(self, name, inherits_from, fields, check_exp, line, column, graph_ref):
        ASTNode.__init__(self, line, column)
        self.name = name  # table name
        self.inherits_from = inherits_from  # optional inheritance
        self.fields = fields  # list of fields
        self.check_exp = check_exp  # Expression to evaluate on insert/update, no need to execute on creation
        self.graph_ref=graph_ref

    def execute(self, table: SymbolTable, tree):
        super().execute(table, tree)
        #result_name = self.name.execute(table, tree)
        result_name = self.name
        result_inherits_from = self.inherits_from.execute(table, tree) if self.inherits_from else None
        result_fields = self.fields
        if result_inherits_from:
            # get inheritance table, if doesn't exists throws semantic error, else append result
            result_fields.append(table.get_fields_from_table(result_inherits_from))


        result = createTable(table.get_current_db().name, result_name, len(result_fields))    

        if result == 1:
            raise Error(0, 0, ErrorType.RUNTIME, '5800: system_error')
            return False
        elif result == 2:
            raise Error(0, 0, ErrorType.RUNTIME, '42P04: database_does_not_exists')
            return False
        elif result == 3:
            raise Error(0, 0, ErrorType.RUNTIME, '42P07: duplicate_table')
            return False
        else:
            #add primary keys, jsonMode needs the number of the column to set it to primarykey            
            keys = list( 
                map(
                    lambda x: result_fields.index(x),
                    filter(lambda key: key.is_pk == True, result_fields)                           
                    )  
            )
            if(len(keys)>0):
                result = alterAddPK(table.get_current_db().name, result_name, keys)

            table.add(TableSymbol(table.get_current_db().id, result_name, self.check_exp))

        ##result_fields = self.fields.execute(table, tree)  # A list of TableField assumed

        field_index = 0
        for field in result_fields:
            field.table_name = result_name
            field.field_index = field_index
            field.type = SymbolType.FIELD
            field_index += 1
            table.add(field)
        return "Table: " +str(result_name) +" created."


class TableField(ASTNode):  # returns an item, grammar has to add it to a list and synthesize value to table
    def __init__(self, name, field_type, length, allows_null, is_pk, line, column, graph_ref):
        ASTNode.__init__(self, line, column)
        self.name = name  # field name
        self.field_type = field_type  # type of field
        self.length = length
        self.allows_null = allows_null  # if true then NULL or default, if false the means is NOT NULL
        self.is_pk = is_pk  # field is primary key
        self.graph_ref = graph_ref
    def execute(self, table: SymbolTable, tree):
        super().execute(table, tree)
        result_name = self.name.execute(table, tree)
        result_field_type = self.field_type.execute(table, tree)
        result_length = self.length.execute(table, tree)
        return FieldSymbol(
            table.get_current_db().name,
            None,
            0,
            result_name,
            result_field_type,
            result_length,
            self.allows_null,
            self.is_pk,
            None,
            None
        )


# table = SymbolTable([])
# cdb_obj = CreateDatabase('db_test2', None, None, False, 1, 2)
# print(cdb_obj.execute(table, None))
