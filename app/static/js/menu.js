var menu_item = document.querySelectorAll('.item_menu')

function select_link(){
    menu_item.forEach((item)=>
        item.classList.remove('ativo'))
    this.classList.add('ativo')
}

menu_item.forEach((item)=>
    item.addEventListener('click', select_link)
)

//expandir o menu

var btn_exp = document.querySelector('#btn_exp')
var menu_side = document.querySelector('.menu_lateral')

btn_exp.addEventListener('click', function(){
    menu_side.classList.toggle('expandir')
})