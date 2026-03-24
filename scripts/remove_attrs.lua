-- 移除 div 和 span 元素的属性（class, style 等）
function Div(el)
  el.attr = pandoc.Attr()
  return el
end

function Span(el)
  el.attr = pandoc.Attr()
  return el
end
