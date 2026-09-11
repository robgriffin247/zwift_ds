with

source as (
    select 
        *
    from {{ ref("stg_riders") }}
)

select * from source