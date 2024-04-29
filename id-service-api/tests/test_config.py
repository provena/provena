from ProvenaInterfaces.HandleModels import ValueType

test_email = "fake@gmail.com"
stage = "DEV"
handle_service_postfix="/handle/"
mint_endpoint=f"{handle_service_postfix}mint"
add_endpoint=f"{handle_service_postfix}add_value"
add_by_index_endpoint=f"{handle_service_postfix}add_value_by_index"
get_endpoint=f"{handle_service_postfix}get"
list_endpoint=f"{handle_service_postfix}list"
modify_by_index_endpoint=f"{handle_service_postfix}modify_by_index"
remove_by_index_endpoint=f"{handle_service_postfix}remove_by_index"

default_value_type=ValueType.URL

test_url_1="https://test1.com"
test_url_2="https://test2.com"
incorrect_id="fjdsklfjdskl"