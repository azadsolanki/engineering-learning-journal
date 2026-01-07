-- Problem 1: Longest Consecutive Uptime Period (The Classic)

-- Goal: For each server, find the longest period (start date, end date, and total duration) 
--where its status was consistently 'healthy' or 'maintenance' (treating maintenance as acceptable downtime for uptime calculation).

with server_health_check as (
	select 
		*, 
		row_number() over(partition by server_id order by log_date asc) as rn 
	from server_health 
	where status in ('healthy', 'maintenance')	
), 

island_group as (
	select 
		server_id, 
		log_date, 
		log_date - (rn * interval '1 hour') as island_id
	from server_health_check
), 

uptime_period as (
select 
	server_id, 
	island_id,
	min(log_date) as start_date, 
	max(log_date) as end_date ,
	-- (max(log_date) - min(log_date)) as total_duration 
	(count(*) * interval '1 hour') as total_duration, 
	count(*) as log_count
	
from island_group 
group by server_id, island_id
order by start_date asc
)

select 
	server_id, 
	island_id, 
	start_date, 
	end_date, 
	total_duration
from (
	select 
		*, 
		row_number() over(partition by server_id order by log_count desc) as rank_by_duration 
	from uptime_period 
) as ranked_period 
where rank_by_duration = 1
order by server_id





-- Problem 4: Finding Consecutive State Periods

-- Goal: Find the total duration and the start date for all periods where two or more distinct servers were simultaneously reporting an 'unstable' status for at least 6 hours (i.e., the system was collectively unstable).