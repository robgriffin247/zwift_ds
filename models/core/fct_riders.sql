with

source as (
    select 
        *
    from {{ ref("int_riders") }}
)

select * from source