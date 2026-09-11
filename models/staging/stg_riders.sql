with 
source as (
    select
        *
    from {{ source("raw_zwift_racing", "riders") }}   
)

select * from source