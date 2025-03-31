from typing import Iterable, List, Any, Mapping, Dict

def unserialize(obj,data_type):
    '''
    Unserialize the object to the given data type.
    If the data type has an unserialize method, it will be called.
    Otherwise, the object will be cast to the data type.
    :param obj: The object to unserialize.
    :param data_type: The data type to unserialize to.
    :return: The unserialized object.
    '''
    if hasattr(data_type,'unserialize'):
        return data_type.unserialize(obj)
    else:
        return data_type(obj)

def serialize(obj):
    '''
    Serialize the object to a dictionary.
    If the object has a serialize method, it will be called.
    Otherwise, the object will be cast to a dictionary.
    :param obj: The object to serialize.
    :return: The serialized object.
    '''
    if hasattr(obj,'serialize'):
        return obj.serialize()
    else:
        return obj

class TypedList:
    '''
    A list that only accepts elements of a certain type.
    This is a generic class that can be used to create lists of any type.
    :param var_type: The type of the elements in the list.
    :param iterable: An iterable to initialize the list with.
    :return: A list of the specified type.
    :raises TypeError: If the elements in the iterable are not of the specified type.
    :raises ValueError: If the elements in the iterable are not of the specified type.
    :raises IndexError: If the index is out of range.
    :raises KeyError: If the key is not found in the list.
    :raises AttributeError: If the attribute is not found in the list.
    :raises NotImplementedError: If the class is not implemented.
    :raises Exception: If the class is not implemented.
    :raises AssertionError: If the assertion fails.
    Usage:
    >>> from utils.struct import TypedList
    >>> Ints = TypedList[int]
    >>> a = Ints([0,1,2])
    >>> a.append(3)
    >>> assert isinstance(a,TypedList[int])
    >>> assert serialize(a) == [0,1,2,3]
    >>> assert a[0] == 0
    '''
    memory=dict()
    def __init__(self):
        raise NotImplementedError
    def __class_getitem__(cls,var_type):
        '''
        This method is called when the class is indexed with a type.
        It returns a new class that is a subclass of the original class.
        :param var_type: The type of the elements in the list.
        :return: A new class that is a subclass of the original class.
        :raises TypeError: If the elements in the iterable are not of the specified type.
        :raises ValueError: If the elements in the iterable are not of the specified type.
        :raises IndexError: If the index is out of range.
        :raises KeyError: If the key is not found in the list.
        '''
        if var_type in cls.memory:
            return cls.memory[var_type]
        class temp(List[Any]):
            '''
            A list that only accepts elements of a certain type.
            This is a generic class that can be used to create lists of any type.
            :param var_type: The type of the elements in the list.
            :param iterable: An iterable to initialize the list with.
            :return: A list of the specified type.
            '''
            __name__ = f'List[{var_type.__name__}]'
            def __init__(self, iterable: Iterable[Any] = None):
                '''
                Initialize the list with the given iterable.
                :param iterable: An iterable to initialize the list with.
                '''
                if not iterable:
                    iterable = ()
                if not all(isinstance(item, var_type) for item in iterable):
                    raise TypeError(f"All elements must be of type {var_type.__name__}")
                super().__init__(iterable)
        
            def __setitem__(self, index:int, value: Any):
                if not isinstance(value, var_type):
                    raise TypeError(f"Expected type {var_type.__name__}, got {type(value).__name__}")
                super().__setitem__(index, value)

            def append(self, value: Any):
                if not isinstance(value, var_type):
                    raise TypeError(f"Expected type {var_type.__name__}, got {type(value).__name__}")
                super().append(value)
        
            def extend(self, iterable: Iterable[Any]):
                if not all(isinstance(item, var_type) for item in iterable):
                    raise TypeError(f"All elements must be of type {var_type.__name__}")
                super().extend(iterable)
        
            def insert(self, index: int, value: Any):
                if not isinstance(value, var_type):
                    raise TypeError(f"Expected type {var_type.__name__}, got {type(value).__name__}")
                super().insert(index, value)
            
            def serialize(self):
                return [serialize(i) for i in self]

            @classmethod
            def unserialize(cls, obj):
                assert isinstance(obj,Iterable)
                return cls((unserialize(item,var_type) for item in obj))
                
        temp.__name__ = f'List[{var_type.__name__}]'
        cls.memory[var_type] = temp
        return temp

REQUIRED = object() #Required
FIXED = object() #The value is fixed to be the default value
UNREQUIRED = object() #Not required
NODEFAULT = object() #Only for Required, no default value is given and user must specify
EMPTY = object() #Only for UnRequired, if no value is given, omit the term.
SERIAL_FAIL = object()

class field:
    '''
    A field is a class that represents a field in a component.
    It has three attributes:
    - is_required: Whether the field is required or not.
    - val_type: The type of the field.
    - default_val: The default value of the field.
    :param is_required: Either the field is required, take value from REQUIRED, UNREQUIRED, FIXED
    :param val_type: The type of the field.
    :param default_val: The default value of the field, take value from NODEFAULT, EMPTY
    '''
    def __init__(self,is_required,val_type,default_val):
        self.is_required = is_required
        self.val_type = val_type
        self.default_val = default_val
    
    def check(self,val):
        return isinstance(val,self.val_type)

class component:
    _field_types: Mapping[str,field] = {}
    _is_concrete = False
    _childrens=set()

    '''
    A component is a class that represents a component in a system.
    It has three attributes:
    - _field_types: A dictionary that maps field names to field types.
    - _is_concrete: Whether the component is concrete or not.
    - _childrens: A set of child components.
    Example Usage:
    Construction:
    >>> from utils.struct import component, field, REQUIRED, UNREQUIRED, FIXED, NODEFAULT, EMPTY
    >>> class MyComponent(component):
    ...     _field_types = {
    ...         'name': field(REQUIRED, str, NODEFAULT),
    ...         'age': field(UNREQUIRED, int, 0),
    ...         'address': field(UNREQUIRED, str, EMPTY)
    ...     }
    >>> my_component = MyComponent(name='John', age=30)
    >>> assert my_component.name == 'John'

    Unserialize:
    >>> from utils.struct import unserialize
    >>> data = {'name': 'John', 'age': 30}
    >>> my_component = unserialize(data, MyComponent)
    >>> assert my_component.name == 'John'
    '''
    
    def __init__(self,*args,**kargs):
        self._field_values = {}
        for key,val in kargs.items():
            self.__setattr__(key,val)
    
    def __setattr__(self,key:str,val:object,strict:bool=True):
        if key.startswith('_'):
            super().__setattr__(key,val)
        elif key in self._field_types:
            types = self._field_types[key]
            assert types.check(val), f"For {key}, {val} is not of type {types.val_type}"
            if types.is_required == FIXED:
                assert val == types.default_val, f"For {key}, must be {types.default_val}, got {val} instead!"
            self._field_values[key] = val
        elif not strict:
            self._field_values[key] = val
            print(key)
            self._field_types[key] = field(UNREQUIRED,object,EMPTY)
        else:
            raise ValueError(f"{key} does not exists for Component {self.__name__}!")
    
    def get_type(self,attr_name):
        if attr_name in self._field_types:
            attr_field = self._field_types[attr_name]
            return attr_field.val_type
        else:
            raise KeyError
    
    def __getattr__(self,key,def_val=None):
        return self._field_values.get(key,def_val)
    
    def __init_subclass__(cls,*args,**kwargs):
        super().__init_subclass__(**kwargs)
        base_fields = getattr(cls, '_field_types', {}).copy()  # Copy parent fields
        meta_add = getattr(cls, '_meta_add',{})
        meta_omit = getattr(cls, '_meta_omit',set())
        for field in meta_omit:
            base_fields.pop(field, None)
        base_fields.update(meta_add)
        cls._field_types = base_fields
        
        direct_parent:component = cls.__bases__[0]
        if not hasattr(direct_parent,'_childrens'):
            direct_parent._childrens = set()
        direct_parent._childrens.add(cls)
        cls._childrens=set()
    
    def serialize(self):
        result = dict()
        for field_name,field_type in self._field_types.items():
            if field_type.is_required == REQUIRED:
                assert (field_name in self._field_values) or field_type.default_val != NODEFAULT
                field_value = self._field_values.get(field_name,field_type.default_val)
                result[field_name] = serialize(field_value)
            elif field_type.is_required == UNREQUIRED:
                field_value = self._field_values.get(field_name,field_type.default_val)
                if field_type.default_val == field_value:continue
                result[field_name] = serialize(field_value)
            elif field_type.is_required == FIXED:
                result[field_name] = serialize(field_type.default_val)
        return result

    @classmethod
    def unserialize(cls,object:Dict):
        if cls._is_concrete:
            res_tmp = cls()
            #for key,val in object.items():
            #    res_tmp.__setattr__(key,unserialize(val,cls._field_types[key].val_type),strict=True)
            #return res_tmp
            try:
                for key,val in object.items():
                    res_tmp.__setattr__(key,unserialize(val,cls._field_types[key].val_type),strict=True)
            except Exception as e:
                print(e)
                return SERIAL_FAIL
            return res_tmp
        else:
            if not hasattr(cls,'_childrens'):
                return SERIAL_FAIL
            for subclass in cls._childrens:
                res = unserialize(object,subclass)
                if res == SERIAL_FAIL:
                    continue
                return res
            return SERIAL_FAIL
    
    @classmethod
    def get_type(cls,attr_name):
        if attr_name in cls._field_types:
            attr_field = cls._field_types[attr_name]
            return attr_field.val_type
        else:
            raise KeyError
    
    @classmethod
    def requirement(cls):
        description = ''
        for field_name,field_type in cls._field_types.items():
            def_val = field_type.default_val
            if hasattr(def_val,'__hash__') and def_val.__hash__ and field_type.default_val in DEFAULT_MAP:
                default_val = DEFAULT_MAP[field_type.default_val]
            else:
                default_val = field_type.default_val
            description += f'{field_name}\t'+REQUIREMENT_MAP[field_type.is_required]+f'\t{field_type.val_type.__name__}\t'+str(default_val)+'\n'
        return description

REQUIREMENT_MAP = {REQUIRED:'必填',
                   FIXED:'固定值',
                   UNREQUIRED:'选填'}
DEFAULT_MAP = {NODEFAULT:'无默认值',
               EMPTY:'可无此字段'}

if __name__ == '__main__':
    Ints = TypedList[int]
    a = Ints([0,1,2])
    a.append(3)
    assert isinstance(a,TypedList[int])
    assert serialize(a) == [0,1,2,3]
    class abs_type(component):
        pass
    class DUM_TEST(abs_type):
        _is_concrete = True
        _meta_add = dict(val = field(UNREQUIRED,str,EMPTY))

    class DUM_TESS(abs_type):
        _is_concrete = True
        _meta_add = dict(value = field(FIXED,str,'hello_bo'))

    class DUM_TESR(abs_type):
        _is_concrete = True
        _meta_add = dict(value = field(FIXED,str,'hello_boss'))

    assert isinstance(unserialize(dict(value='hello_boss'),abs_type),DUM_TESR)
