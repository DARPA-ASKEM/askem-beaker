using SyntacticModels, Decapodes, Catlab
import JSON3, DisplayAs

_expr = Decapodes.parse_decapode(quote
    {{ declaration }} 
end)
