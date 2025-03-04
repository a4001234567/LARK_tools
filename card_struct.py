from typing import TypeVar, Generic, Iterable, List

class TypedList:
    memory=dict()
    def __init__(self):
        raise NotImplementedError
    def __class_getitem__(cls,var_type):
        if var_type in cls.memory:
            return cls.memory[var_type]
        class temp(List[var_type]):
            __name__ = f'List[{var_type.__name__}]'
            def __init__(self, iterable: Iterable[var_type] = None):
                if not iterable:
                    iterable = ()
                if not all(isinstance(item, var_type) for item in iterable):
                    raise TypeError(f"All elements must be of type {var_tyle.__name__}")
                super().__init__(iterable)
        
            def __setitem__(self, index, value: var_type):
                if not isinstance(value, var_type):
                    raise TypeError(f"Expected type {var_type.__name__}, got {type(value).__name__}")
                super().__setitem__(index, value)
        
            def append(self, value: var_type):
                if not isinstance(value, var_type):
                    raise TypeError(f"Expected type {var_type.__name__}, got {type(value).__name__}")
                super().append(value)
        
            def extend(self, iterable: Iterable[var_type]):
                if not all(isinstance(item, var_type) for item in iterable):
                    raise TypeError(f"All elements must be of type {var_type.__name__}")
                super().extend(iterable)
        
            def insert(self, index: int, value: var_type):
                if not isinstance(value, var_type):
                    raise TypeError(f"Expected type {var_type.__name__}, got {type(value).__name__}")
                super().insert(index, value)
            
            def serialize(self):
                if hasattr(var_type,'serialize'):
                    return [i.serialize() for i in self]
                else:
                    return list(self)
        temp.__name__ = f'List[{var_type.__name__}]'
        cls.memory[var_type] = temp
        return temp

ints = TypedList[int]
a = ints([0,1,2])
a.append(3)
assert isinstance(a,TypedList[int])
assert a.serialize() == [0,1,2,3]

REQUIRED = object() #Required
FIXED = object() #The value is fixed to be the default value
UNREQUIRED = object() #Not required
NODEFAULT = object() #Only for Required, no default value is given and user must specify
EMPTY = object() #Only for UnRequired, if no value is given, omit the term.
class field:
    def __init__(self,is_required,val_type,default_val):
        self.is_required = is_required
        self.val_type = val_type
        self.default_val = default_val
    def check(self,val):
        return isinstance(val,self.val_type)
    
class component:
    _field_types = {}
    def __init__(self,*args,**kargs):
        self._field_values = {}
        for key,val in kargs.items():
            self.__setattr__(key,val)
    def __setattr__(self,key,val):
        if key.startswith('_'):
            super().__setattr__(key,val)
        else:
            if key in self._field_types:
                types = self._field_types[key]
                assert types.check(val)
                self._field_values[key] = val
            else:
                self._field_values[key] = val
                self._field_types[key] = field(UNREQUIRED,object,EMPTY)
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
    def serialize(self):
        def _temp(var):
            if hasattr(var,'serialize'):
                return var.serialize()
            else:
                return var
        result = dict()
        for field_name,field_type in self._field_types.items():
            if field_type.is_required == REQUIRED:
                assert (field_name in self._field_values) or field_type.default_val != NODEFAULT
                field_value = self._field_values.get(field_name,field_type.default_val)
                result[field_name] = _temp(field_value)
            elif field_type.is_required == UNREQUIRED:
                field_value = self._field_values.get(field_name,field_type.default_val)
                if field_type.default_val == field_value:continue
                #if field_type.default_val in (field_value,NODEFAULT,EMPTY):continue
                result[field_name] = _temp(field_value)
            elif field_type.is_required == FIXED:
                result[field_name] = _temp(field_type.default_val)
        return result
    
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

class text(component):
    pass
class plain_text(text):
    _meta_add = dict(tag = field(FIXED,str,'plain_text'),
                     content = field(REQUIRED,str,NODEFAULT)
                    )
class markdown(text):
    _meta_add = dict(tag = field(FIXED,str,'markdown'),
                     content = field(REQUIRED,str,NODEFAULT)
                    )

class icon(component):
    pass

class cp_header_icon(icon):
    _meta_add = dict(tag = field(REQUIRED,str,NODEFAULT),
                     token = field(UNREQUIRED,str,EMPTY),
                     color = field(UNREQUIRED,str,EMPTY),
                     img_key = field(UNREQUIRED,str,EMPTY),
                     size = field(UNREQUIRED,str,'10px 10px')
                    )

class element(component):
    _meta_add = dict(tag = field(REQUIRED,str,'element'),
                     element_id = field(UNREQUIRED,str,EMPTY)
                    )

Elements = TypedList[element]

class container(element):
   _meta_add = dict(tag = field(FIXED,str,'container'),
                    element_id = field(UNREQUIRED,str,EMPTY),
                    margin = field(UNREQUIRED,str,'0px'),
                    horizontal_spacing = field(UNREQUIRED,str,'8px'),
                    horizontal_align = field(UNREQUIRED,str,'left'),
                    vertical_spacing = field(UNREQUIRED,str,'12px'),
                    vertical_align = field(UNREQUIRED,str,'top'),
                    elements = field(UNREQUIRED,Elements,EMPTY)
                   )

class multi_url(component):
    _meta_add = dict(url = field(UNREQUIRED,str,EMPTY),
                     android_url = field(UNREQUIRED,str,EMPTY),
                     ios_url = field(UNREQUIRED,str,EMPTY),
                     pc_url = field(UNREQUIRED,str,EMPTY)
                    )

class action(component):
    _meta_add = dict(multi_url = field(UNREQUIRED,multi_url,EMPTY))
Actions = TypedList[action]

class behavior(component):
    _meta_add = dict(type = field(FIXED,str,'behavior'))

class open_url(behavior):
    _meta_add = dict(type = field(FIXED,str,'open_url'),
                     default_url = field(REQUIRED,str,NODEFAULT),
                     android_url = field(UNREQUIRED,str,EMPTY),
                     ios_url = field(UNREQUIRED,str,EMPTY),
                     pc_url = field(UNREQUIRED,str,EMPTY)
                    )
class call_back(behavior):
    _meta_add = dict(type = field(FIXED,str,'callback'),
                     value = field(REQUIRED,object,NODEFAULT)
                    )

class form_action(behavior):
    _meta_add = dict(type = field(FIXED,str,'form_action'),
                     behavior = field(REQUIRED,str,NODEFAULT)
                    )
Behaviors = TypedList[behavior]

class column(container):
    _meta_add = dict(tag = field(FIXED,str,'column'),
                     background_style = field(UNREQUIRED,str,'default'),
                     width = field(UNREQUIRED,str,'auto'),
                     weight = field(UNREQUIRED,int,1),
                     vertical_spacing = field(UNREQUIRED,str,'8px'),
                     direction = field(UNREQUIRED,str,'vertical'),
                     padding = field(UNREQUIRED,str,'0px'),
                     elements = field(UNREQUIRED,Elements,EMPTY),##TODO: can it be empty?
                     action = field(UNREQUIRED,action,EMPTY)
                    )

Columns = TypedList[column]

class column_set(container):
    _meta_omit = {'vertical_spacing',
                  'elements'}
    _meta_add = dict(tag = field(FIXED,str,'column_set'),
                     flex_mode = field(UNREQUIRED,str,None),
                     background_style = field(UNREQUIRED,str,'default'),
                     action = field(UNREQUIRED,action,EMPTY),
                     columns = field(REQUIRED,Columns,Columns())
                    )

#cyclic?

class form(container):
    _meta_add = dict(tag = field(FIXED,str,'form'),
                     direction = field(REQUIRED,str,'vertical'),
                     margin = field(UNREQUIRED,str,'0px'),
                     padding = field(UNREQUIRED,str,'0px'),
                     name = field(REQUIRED,str,NODEFAULT)
                    )

class ic_confirmation(component):
    _meta_add = dict(title = field(REQUIRED,plain_text,NODEFAULT),
                     text = field(REQUIRED,plain_text,NODEFAULT)
                    )
                 

class interactive_container(container):
    _meta_add = dict(tag = field(FIXED,str,'interactive_container'),
                     width = field(UNREQUIRED,str,'fill'),
                     height = field(UNREQUIRED,str,'auto'),
                     direction = field(UNREQUIRED,str,'vertical'),
                     background_style = field(UNREQUIRED,str,'default'),
                     has_border = field(UNREQUIRED,bool,False),
                     border_color = field(UNREQUIRED,str,'grey'),
                     corner_radius = field(UNREQUIRED,str,'0px'),
                     padding = field(UNREQUIRED,str,'4px,12px'),
                     behaviors = field(REQUIRED,Behaviors,NODEFAULT),
                     hover_tips = field(REQUIRED,plain_text,EMPTY),
                     disabled = field(UNREQUIRED,bool,False),
                     disabled_tips = field(UNREQUIRED,plain_text,EMPTY),
                     confirm = field(UNREQUIRED,ic_confirmation,EMPTY)
                    )
class cp_header(component):
    _meta_add = dict(title = field(REQUIRED,text,NODEFAULT),
                     background_color = field(UNREQUIRED,str,EMPTY),
                     width = field(UNREQUIRED,str,'fill'),
                     vertical_align = field(UNREQUIRED,str,'center'),
                     padding = field(UNREQUIRED,str,'0px'),
                     icon = field(UNREQUIRED,cp_header_icon,EMPTY),
                     icon_position = field(UNREQUIRED,str,'right'),
                     icon_expanded_angle = field(UNREQUIRED,int,180)
                    )
                     
class cp_border(component):
    _meta_add = dict(color=field(UNREQUIRED,str,'grey'),
                     corner_radius = field(UNREQUIRED,str,'5px')
                    )
class collapsible_panel(container):
    _meta_add = dict(tag = field(FIXED,str,'collapsible_panel'),
                     expanded = field(UNREQUIRED,bool,False),
                     direction = field(UNREQUIRED,str,'vertical'),
                     padding = field(UNREQUIRED,str,'0px'),
                     background_color = field(UNREQUIRED,str,EMPTY),
                     header = field(REQUIRED,cp_header,NODEFAULT),
                     border = field(UNREQUIRED,cp_border,EMPTY),
                     elements = field(UNREQUIRED,Elements,EMPTY)##TODO: can it be empty?
                    )

class config_i18n_content(component):
        _meta_add = dict(zh_cn = field(UNREQUIRED,str,EMPTY),
                         en_us = field(UNREQUIRED,str,EMPTY),
                         ja_jp = field(UNREQUIRED,str,EMPTY),
                         zh_hk = field(UNREQUIRED,str,EMPTY),
                         zh_tw = field(UNREQUIRED,str,EMPTY),
                         id_id = field(UNREQUIRED,str,EMPTY),
                         vi_vn = field(UNREQUIRED,str,EMPTY),
                         th_th = field(UNREQUIRED,str,EMPTY),
                         pt_br = field(UNREQUIRED,str,EMPTY),
                         es_es = field(UNREQUIRED,str,EMPTY),
                         ko_kr = field(UNREQUIRED,str,EMPTY),
                         de_de = field(UNREQUIRED,str,EMPTY),
                         fr_fr = field(UNREQUIRED,str,EMPTY),
                         it_it = field(UNREQUIRED,str,EMPTY),
                         ru_ru = field(UNREQUIRED,str,EMPTY),
                         ms_my = field(UNREQUIRED,str,EMPTY)
                        )

class config_summary(component):
    _meta_add = dict(content = field(UNREQUIRED,str,'生成中'),
                     i18n_content = field(UNREQUIRED,config_i18n_content,EMPTY)
                    )

class text_size(component):
    pass

class custom_text_size(component):
    _meta_add = dict(default = field(UNREQUIRED,str,EMPTY),
                     pc = field(UNREQUIRED,str,EMPTY),
                     mobile = field(UNREQUIRED,str,EMPTY)
                    )
class color(component):
    pass

class custom_color(component):
    _meta_add = dict(light_mode = field(REQUIRED,str,NODEFAULT),
                     dark_mode = field(REQUIRED,str,NODEFAULT)
                    )

class config_style(component):
    _meta_add = dict(text_size = field(UNREQUIRED,text_size,EMPTY),
                     color = field(UNREQUIRED,color,EMPTY)
                    )
class config_streaming_config(component):
    _meta_add = dict(print_frequency_ms = field,
                     print_step = field,
                     print_strategy = field
                    )

class body(component):
    _meta_add = dict(elements = field(REQUIRED,Elements,NODEFAULT))
class config(component):
    _meta_add = dict(streaming_mode = field(UNREQUIRED,bool,False),
                     streaming_config = field(UNREQUIRED,config_streaming_config,EMPTY),
                     summary = field(UNREQUIRED,config_summary,EMPTY),
                     enable_forward = field(UNREQUIRED,bool,True),
                     update_multi = field(UNREQUIRED,bool,True),
                     width_mode = field(UNREQUIRED,str,'default'),
                     use_custom_translation = field(UNREQUIRED,bool,False),
                     enable_forward_interaction = field(UNREQUIRED,bool,False),
                     style = field(UNREQUIRED,config_style,EMPTY)
                    )

class link(component):
    _meta_add = dict(url = field(UNREQUIRED,str,EMPTY),
                     pc_url = field(UNREQUIRED,str,EMPTY),
                     ios_url = field(UNREQUIRED,str,EMPTY),
                     android_url = field(UNREQUIRED,str,EMPTY)
                    )

class header_icon(component):
    _meta_add = dict(img_key = field(REQUIRED,str,NODEFAULT))
class header_ud_icon_style(component):
    _meta_add = dict(color = field(REQUIRED,str,NODEFAULT))
class header_ud_icon(component):
    _meat_add = dict(token = field(REQUIRED,str,NODEFAULT),
                     style = field(UNREQUIRED,header_ud_icon_style,EMPTY)
                    )

class text_tag(component):
    _meta_add = dict(tag = field(FIXED,str,'text_tag'),
                     element_id = field(UNREQUIRED,str,EMPTY),
                     text = field(UNREQUIRED,plain_text,EMPTY),##TODO: can it be empty?
                     color = field(UNREQUIRED,str,'blue')
                    )
Text_tags = TypedList[text_tag]
class i18n_text_tag_list(component):
    _meta_add = dict(zh_cn = field(UNREQUIRED,Text_tags,Text_tags()),
                     en_us = field(UNREQUIRED,Text_tags,Text_tags()),
                     ja_jp = field(UNREQUIRED,Text_tags,Text_tags()),
                     zh_hk = field(UNREQUIRED,Text_tags,Text_tags()),
                     zh_tw = field(UNREQUIRED,Text_tags,Text_tags()),
                     id_id = field(UNREQUIRED,Text_tags,Text_tags()),
                     vi_vn = field(UNREQUIRED,Text_tags,Text_tags()),
                     th_th = field(UNREQUIRED,Text_tags,Text_tags()),
                     pt_br = field(UNREQUIRED,Text_tags,Text_tags()),
                     es_es = field(UNREQUIRED,Text_tags,Text_tags()),
                     ko_kr = field(UNREQUIRED,Text_tags,Text_tags()),
                     de_de = field(UNREQUIRED,Text_tags,Text_tags()),
                     fr_fr = field(UNREQUIRED,Text_tags,Text_tags()),
                     it_it = field(UNREQUIRED,Text_tags,Text_tags()),
                     ru_ru = field(UNREQUIRED,Text_tags,Text_tags()),
                     ms_my = field(UNREQUIRED,Text_tags,Text_tags())
                    )
class header(component):
    _meta_add = dict(title = field(REQUIRED,text,NODEFAULT),
                     subtitle = field(UNREQUIRED,text,NODEFAULT),
                     text_tag_list = field(UNREQUIRED,Text_tags,EMPTY),
                     i18n_text_tag_list = field(UNREQUIRED,i18n_text_tag_list,EMPTY),
                     template = field(UNREQUIRED,str,EMPTY),
                     icon = field(UNREQUIRED,header_icon,EMPTY),
                     ud_icon = field(UNREQUIRED,header_ud_icon,EMPTY),
                     padding = field(UNREQUIRED,str,'0')
                    )

class card(component):
    _meta_add = dict(schema = field(FIXED,str,'2.0'),
                     config = field(UNREQUIRED,config,EMPTY),
                     card_link = field(UNREQUIRED,link,EMPTY),
                     header = field(UNREQUIRED,header,EMPTY),
                     body = field(UNREQUIRED,body,EMPTY)
                    )

class presenter(element):
    _meta_add = dict(tag = field(FIXED,str,'presenter'),
                     element_id = field(UNREQUIRED,str,EMPTY),
                     margin = field(UNREQUIRED,str,'0'))

class div_text(component):
    _meta_add = dict(tag = field(REQUIRED,str,'plain_text'),
                     content = field(REQUIRED,str,NODEFAULT),
                     text_size = field(UNREQUIRED,str,'normal'),
                     text_color = field(UNREQUIRED,str,'default'),
                     text_align = field(UNREQUIRED,str,'left'),
                     lines = field(UNREQUIRED,int,EMPTY))

class div_icon(component):
    _meta_add = dict(tag = field(REQUIRED,str,NODEFAULT),
                     token = field(UNREQUIRED,str,EMPTY),
                     color = field(UNREQUIRED,str,EMPTY),
                     img_key = field(UNREQUIRED,str,EMPTY))

class div(presenter):
    _meta_add = dict(tag = field(FIXED,str,'div'),
                     width = field(UNREQUIRED,str,'fill'),
                     text = field(UNREQUIRED,div_text,EMPTY),
                     icon = field(UNREQUIRED,div_icon,EMPTY)
                    )

class markdown(presenter):
    _meta_add = dict(tag = field(FIXED,str,'markdown'),
                     text_align = field(UNREQUIRED,str,'left'),
                     text_size = field(UNREQUIRED,str,'normal'),
                     content = field(UNREQUIRED,str,EMPTY),
                     icon = field(UNREQUIRED,div_icon,EMPTY)
                    )

class img(presenter):
    _meta_add = dict(tag = field(FIXED,str,'img'),
                     img_key = field(UNREQUIRED,str,NODEFAULT),
                     alt = field(REQUIRED,plain_text,NODEFAULT),
                     title = field(UNREQUIRED,plain_text,NODEFAULT),
                     corner_radius = field(UNREQUIRED,text,EMPTY),
                     scale_type = field(UNREQUIRED,str,'crop_center'),
                     size = field(UNREQUIRED,str,EMPTY),
                     transparent = field(UNREQUIRED,bool,False),
                     preview = field(UNREQUIRED,bool,True)
                    )

class img_combination_img(component):
    _meta_add = dict(img_key = field(REQUIRED,str,NODEFAULT))
Img_combination_imgs = TypedList[img_combination_img]

class img_combination(presenter):
    _meta_add = dict(tag = field(FIXED,str,'img_combination'),
                     combination_mode = field(REQUIRED,str,NODEFAULT),
                     corner_radius = field(UNREQUIRED,text,EMPTY),
                     img_list = field(REQUIRED,Img_combination_imgs,NODEFAULT),
                     combination_transparent = field(UNREQUIRED,bool,False)
                    )

class person(presenter):
    _meta_add = dict(tag = field(FIXED,str,'person'),
                     size = field(UNREQUIRED,str,'medium'),
                     show_avator = field(UNREQUIRED,bool,False),
                     show_name = field(UNREQUIRED,bool,True),
                     style = field(UNREQUIRED,str,'normal'),
                     user_id = field(REQUIRED,str,EMPTY)
                    )

class person_list_person(component):
    _meta_add = dict(id = field(REQUIRED,str,NODEFAULT))
Person_list_persons = TypedList[person_list_person]

class person_list(presenter):
    _meta_add = dict(tag = field(FIXED,str,'person_list'),
                     drop_invalid_user_id = field(UNREQUIRED,bool,False),
                     lines = field(UNREQUIRED,int,EMPTY),
                     show_name = field(UNREQUIRED,bool,True),
                     show_avator = field(UNREQUIRED,bool,False),
                     size = field(UNREQUIRED,str,'medium'),
                     persons = field(REQUIRED,Person_list_persons,NODEFAULT),
                     icon = field(UNREQUIRED,div_icon,EMPTY),
                     ud_icon = field(UNREQUIRED,header_ud_icon,EMPTY))

class VChartSpec(component):
    pass
    

class chart(presenter):
    _meta_add = dict(tag = field(FIXED,str,'chart'),
                     aspect_ratio = field(UNREQUIRED,str,EMPTY),
                     color_theme = field(UNREQUIRED,str,'brand'),
                     chart_spec = field(REQUIRED,VChartSpec,NODEFAULT),
                     preview = field(UNREQUIRED,bool,True),
                     height = field(UNREQUIRED,str,'auto'))

class header_style(component):
    _meta_add = dict(text_align = field(UNREQUIRED,str,'left'),
                     text_size = field(UNREQUIRED,str,'normal'),
                     background_style = field(UNREQUIRED,str,None),
                     text_color = field(UNREQUIRED,str,'default'),
                     bold = field(UNREQUIRED,bool,True),
                     lines = field(UNREQUIRED,int,1)
                    )

class column_format(component):
    _meta_add = dict(precision = field(UNREQUIRED,int,EMPTY),
                     symbol = field(UNREQUIRED,str,EMPTY),
                     separator = field(UNREQUIRED,bool,False)
                    )
class column(component):
    _meta_add = dict(name = field(REQUIRED,str,NODEFAULT),
                     display_name = field(UNREQUIRED,str,EMPTY),
                     width = field(UNREQUIRED,str,'auto'),
                     vertical_align = field(UNREQUIRED,str,'center'),
                     horizontal_align = field(UNREQUIRED,str,'left'),
                     data_type = field(REQUIRED,str,'text'),
                     format = field(UNREQUIRED,column_format,EMPTY),
                     date_format = field(UNREQUIRED,str,EMPTY)
                    )
Columns = TypedList[column]

class table(presenter):
    _meta_add = dict(tag = field(FIXED,str,'table'),
                     page_size = field(UNREQUIRED,int,5),
                     row_height = field(UNREQUIRED,str,'low'),
                     row_max_height = field(UNREQUIRED,str,'124px'),
                     header_style = field(UNREQUIRED,header_style,EMPTY),
                     freeze_first_column = field(UNREQUIRED,bool,False),
                     columns = field(REQUIRED,Columns,Columns()),
                     rows = field(REQUIRED,TypedList[dict],TypedList[dict]()))
    def __init__(self,*args,**kargs):
        super().__init__(*args,**kargs)

class hr(presenter):
    _meta_add = dict(tag = field(FIXED,str,'hr'))

class confirm(component):
    _meta_add = dict(title = field(REQUIRED,plain_text,NODEFAULT),
                     text = field(REQUIRED,plain_text,NODEFAULT))
class fallback(component):
    _meta_add = dict(tag = field(FIXED,str,'fallback_text'),
                     text = field(REQUIRED,plain_text,NODEFAULT))
                     
class interactive(element):
    _meta_add = dict(tag = field(FIXED,str,'interactive'),
                     element_id = field(UNREQUIRED,str,EMPTY),
                     margin = field(UNREQUIRED,str,'0px'),
                     confirm = field(UNREQUIRED,confirm,EMPTY),
                     value = field(UNREQUIRED,object,EMPTY),
                     name = field(UNREQUIRED,str,EMPTY),
                     width = field(UNREQUIRED,str,'default'),
                     behaviors = field(REQUIRED,Behaviors,NODEFAULT)
                    )

class input(interactive):
    _meta_add = dict(tag = field(FIXED,str,'input'),
                     required = field(UNREQUIRED,bool,False),
                     disabled = field(UNREQUIRED,bool,False),
                     disabled_tips = field(UNREQUIRED,plain_text,EMPTY),
                     placeholder = field(UNREQUIRED,plain_text,EMPTY),
                     default_value = field(UNREQUIRED,str,EMPTY),
                     max_length = field(UNREQUIRED,int,1000),
                     input_type = field(UNREQUIRED,str,'text'),
                     show_icon = field(UNREQUIRED,bool,True),
                     rows = field(UNREQUIRED,int,5),
                     auto_resize = field(UNREQUIRED,bool,False),
                     max_rows = field(UNREQUIRED,int,EMPTY),
                     label = field(UNREQUIRED,plain_text,EMPTY),
                     label_position = field(UNREQUIRED,str,'top')
                    )
    _meta_omit = {'behaviors'}

class button(interactive):
    _meta_add = dict(tag = field(FIXED,str,'button'),
                     type = field(UNREQUIRED,str,'default'),
                     size = field(UNREQUIRED,str,'medium'),
                     text = field(UNREQUIRED,plain_text,EMPTY),
                     icon = field(UNREQUIRED,div_icon,EMPTY),
                     hover_tips = field(UNREQUIRED,plain_text,EMPTY),
                     disabled = field(UNREQUIRED,bool,False),
                     disabled_tips = field(UNREQUIRED,plain_text,EMPTY),
                     required = field(UNREQUIRED,bool,False),
                     behaviors = field(UNREQUIRED,Behaviors,NODEFAULT),
                     action_type = field(UNREQUIRED,str,EMPTY)
                 )
    _meta_omit = {'value'}

class overflow_option(component):
    _meta_add = dict(text = field(REQUIRED,plain_text,'EMPTY'),
                     multi_url = field(UNREQUIRED,multi_url,'EMPTY'),
                     value = field(UNREQUIRED,object,'EMPTY'))

class overflow(interactive):
    _meta_add = dict(tag = field(FIXED,str,'overflow'),
                     options = field(REQUIRED,overflow_option,EMPTY)
                    )
    _meta_omit = {'name','behaviors'}

class select_static_option(component):
    _meta_add = dict(text = field(REQUIRED,plain_text,NODEFAULT),
                     icon = field(UNREQUIRED,div_icon,EMPTY),
                     value = field(REQUIRED,str,NODEFAULT))

class select_static(interactive):
    _meta_add = dict(tag = field(FIXED,str,'select_static'),
                     type = field(UNREQUIRED,str,'default'),
                     required = field(UNREQUIRED,bool,False),
                     disabled = field(UNREQUIRED,bool,False),
                     inital_option = field(UNREQUIRED,str,EMPTY),
                     placeholder = field(UNREQUIRED,plain_text,EMPTY),
                     options = field(REQUIRED,TypedList[select_static_option],EMPTY)
                    )
    _meta_omit = {'value'}

class multi_select_static(interactive):
    _meta_add = dict(tag = field(FIXED,str,'multi_select_static'),
                     name = field(REQUIRED,str,EMPTY),
                     placeholder = field(UNREQUIRED,plain_text,EMPTY),
                     required = field(UNREQUIRED,bool,False),
                     disabled = field(UNREQUIRED,bool,False),
                     selected_values = field(UNREQUIRED,TypedList[str],TypedList[str]()),
                     options = field(REQUIRED,TypedList[select_static_option],EMPTY),
                     type = field(UNREQUIRED,str,'default')
                    )
    _meta_omit = {'value'}

class person_option(component):
    _meta_add = dict(value = field(REQUIRED,str,NODEFAULT))
Person_options = TypedList[person_option]

class select_person(interactive):
    _meta_add = dict(tag = field(FIXED,str,'select_person'),
                     type = field(UNREQUIRED,str,'default'),
                     required = field(UNREQUIRED,bool,False),
                     disabled = field(UNREQUIRED,bool,False),
                     placeholder = field(UNREQUIRED,plain_text,EMPTY),
                     options = field(UNREQUIRED,Person_options,EMPTY)
                    )
    _meta_omit = {'name','value'}

class multi_select_person(interactive):
    _meta_add = dict(tag = field(FIXED,str,'multi_select_person'),
                     type = field(UNREQUIRED,str,'default'),
                     required = field(UNREQUIRED,bool,False),
                     disabled = field(UNREQUIRED,bool,False),
                     placeholder = field(UNREQUIRED,plain_text,EMPTY),
                     selected_values = field(UNREQUIRED,TypedList[str],EMPTY),
                     options = field(UNREQUIRED,Person_options,EMPTY)
                    )


class date_picker(interactive):
    _meta_add = dict(tag = field(FIXED,str,'date_picker'),
                     required = field(UNREQUIRED,bool,False),
                     disabled = field(UNREQUIRED,bool,False),
                     placeholder = field(UNREQUIRED,plain_text,EMPTY),
                     initial_date = field(UNREQUIRED,str,EMPTY)
                    )

class picker_time(interactive):
    _meta_add = dict(tag = field(FIXED,str,'picker_time'),
                     required = field(UNREQUIRED,bool,False),
                     disabled = field(UNREQUIRED,bool,False),
                     placeholder = field(UNREQUIRED,plain_text,EMPTY),
                     initial_time = field(UNREQUIRED,str,EMPTY)
                    )

class picker_datetime(interactive):
    _meta_add = dict(tag = field(FIXED,str,'picker_datetime'),
                     required = field(UNREQUIRED,bool,False),
                     disabled = field(UNREQUIRED,bool,False),
                     placeholder = field(UNREQUIRED,plain_text,EMPTY),
                     initial_datetime = field(UNREQUIRED,str,EMPTY)
                    )


class img_option(component):
    _meta_add = dict(img_key = field(REQUIRED,str,NODEFAULT),
                     value = field(UNREQUIRED,str,EMPTY),
                     disabled = field(UNREQUIRED,bool,False),
                     disabled_tips = field(UNREQUIRED,plain_text,EMPTY),
                     hover_tips = field(UNREQUIRED,plain_text,EMPTY)
                    )
Img_options = TypedList[img_option]

class select_img(interactive):
    _meta_add = dict(tag = field(FIXED,str,'select_img'),
                     multi_select = field(UNREQUIRED,bool,False),
                     layout = field(UNREQUIRED,str,'bisect'),
                     required = field(UNREQUIRED,bool,False),
                     can_preview = field(UNREQUIRED,bool,True),
                     aspect_ratio = field(UNREQUIRED,str,'16:9'),
                     disabled = field(UNREQUIRED,bool,False),
                     disabled_tips = field(UNREQUIRED,plain_text,EMPTY),
                     options = field(REQUIRED,Img_options,NODEFAULT)
                    )
    _meta_omit = {'width'}
    
class checker_text(component):
    _meta_add = dict(tag = field(REQUIRED,str,'plain_text'),
                     content = field(REQUIRED,str,NODEFAULT),
                     text_size = field(UNREQUIRED,str,'normal'),
                     text_color = field(UNREQUIRED,str,'default'),
                     text_align = field(UNREQUIRED,str,'left')
                    )

class checker_check_style(component):
    _meta_add = dict(show_strikethrough=field(UNREQUIRED,bool,False),
                     opacity = field(UNREQUIRED,float,1.)
                    )

class checker_button_area(component):
    _meta_add = dict(pc_display_rule = field(UNREQUIRED,str,'always'),
                     buttons = field(UNREQUIRED,TypedList[button],EMPTY)
                    )

class checker(interactive):
    _meta_add = dict(tag = field(FIXED,str,'checker'),
                     checked = field(UNREQUIRED,bool,False),
                     text = field(UNREQUIRED,checker_text,EMPTY),
                     overall_checkable = field(UNREQUIRED,bool,True),
                     button_area = field(UNREQUIRED,checker_button_area,EMPTY),
                     checked_style = field(UNREQUIRED,checker_check_style,EMPTY),
                     padding = field(UNREQUIRED,str,'0px'),
                     hover_tips = field(UNREQUIRED,plain_text,EMPTY),
                     disabled = field(UNREQUIRED,bool,False),
                     disabled_tips = field(UNREQUIRED,plain_text,EMPTY)
                    )
    _meta_omit = {'width','value'}
                     
class VChartSpec(component):
    pass

if __name__ == '__main__':
    demo_card = card()
    demo_card.header = header()
    demo_card.header.title = plain_text(content='标题')
    demo_card.header.subtitle = plain_text(content='副标题')
    demo_card.body = body()
    demo_card.body.elements = Elements()
    form_element = form()
    demo_card.body.elements.append(form_element)
    password_input = input(element_id = 'abcd',
                       name = 'abcd',
                       input_type = 'password',
                       show_icon = True,
                       label = plain_text(content='密码')
                      )
    button_input = button(element_id = 'buttonn',
                        action_type = 'form_submit'
                        )
    form_element.elements = Elements((password_input,button_input))
    form_element.name = 'form'

    import json
    print(json.dumps(json.dumps(demo_card.serialize())))