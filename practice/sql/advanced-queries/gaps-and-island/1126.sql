-- Find all periods where a server had at least 4 consecutive days of healthy status.


with selective_filter as (
	select *, row_number() over(order by log_date asc) row_num 
	from server_health
	where status = 'healthy'
), 

island as (
	select *, log_id - row_num as island_id
	from selective_filter
), 

valid_islands as(
	select island_id, count(*) as island_size
	from island 
	group by island_id
	having count(*) >= 4
)

select i.log_id, i.log_date, i.status, i.cpu_usage 
from island i
join valid_islands v on i.island_id = v.island_id
order by i.log_date


-- Problem 4: Finding Consecutive State Periods

-- Goal: Find the total duration and the start date for all periods where two or more distinct servers were simultaneously reporting an 'unstable' status for at least 6 hours (i.e., the system was collectively unstable).