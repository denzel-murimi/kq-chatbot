-- 002_seed.sql
-- Synthetic booking data for testing the transactional pipeline.
-- The proposal commits to simulated data only; none of this is real passenger data.
--
-- Row 1 is the demo booking the frontend dashboard already references
-- (PNR ABC123, last name Doe, seat 12A, flight KQ 100, NBO->LHR). Keep it
-- first and unchanged so the on-screen booking reference works live in the chat.
--
-- Safe to re-run: the insert skips any row whose (pnr, last_name) already exists.

insert into public.bookings
    (pnr, last_name, first_name, flight_number, origin, destination, departure_time, seat, status)
values
    ('ABC123', 'Doe',       'John',     'KQ 100', 'NBO', 'LHR', '2026-12-18 09:30:00+03', '12A', 'confirmed'),
    ('KQ7X2M', 'Otieno',    'Brian',    'KQ 310', 'NBO', 'CDG', '2026-12-19 23:59:00+03', '4C',  'confirmed'),
    ('ZN4P8Q', 'Wanjiru',   'Grace',    'KQ 762', 'NBO', 'JNB', '2026-12-20 07:15:00+03', '21F', 'confirmed'),
    ('RT9K3L', 'Mwangi',    'Peter',    'KQ 100', 'NBO', 'LHR', '2026-12-18 09:30:00+03', '31A', 'checked-in'),
    ('BX6V1W', 'Achieng',   'Faith',    'KQ 532', 'NBO', 'DXB', '2026-12-21 14:45:00+03', '9D',  'confirmed'),
    ('MC2H7J', 'Kamau',     'Daniel',   'KQ 486', 'MBA', 'NBO', '2026-12-18 06:00:00+03', '14B', 'checked-in'),
    ('QW5D9F', 'Njoroge',   'Mercy',    'KQ 101', 'LHR', 'NBO', '2026-12-22 21:30:00+00', '2A',  'confirmed'),
    ('LP8G4S', 'Kiprop',    'James',    'KQ 744', 'NBO', 'BKK', '2026-12-23 13:20:00+03', '26C', 'delayed'),
    ('VH3T6Y', 'Were',      'Amina',    'KQ 310', 'NBO', 'CDG', '2026-12-19 23:59:00+03', '11E', 'confirmed'),
    ('DF7N2B', 'Chepkoech', 'Ruth',     'KQ 420', 'NBO', 'LOS', '2026-12-24 08:50:00+03', '19A', 'confirmed'),
    ('GK9M5R', 'Omondi',    'Kevin',    'KQ 762', 'NBO', 'JNB', '2026-12-20 07:15:00+03', '7B',  'cancelled'),
    ('JT4C8X', 'Mutua',     'Stella',   'KQ 532', 'NBO', 'DXB', '2026-12-21 14:45:00+03', '33F', 'confirmed'),
    ('WN6B3Z', 'Barasa',    'Victor',   'KQ 486', 'MBA', 'NBO', '2026-12-18 06:00:00+03', '5A',  'confirmed'),
    ('CY1L7P', 'Nduta',     'Caroline', 'KQ 101', 'LHR', 'NBO', '2026-12-22 21:30:00+00', '28D', 'checked-in'),
    ('HR8Q2V', 'Kiplagat',  'Dennis',   'KQ 744', 'NBO', 'BKK', '2026-12-23 13:20:00+03', '12C', 'confirmed'),
    ('SD5F9K', 'Atieno',    'Joan',     'KQ 420', 'NBO', 'LOS', '2026-12-24 08:50:00+03', '3B',  'confirmed'),
    ('ZQ3W6M', 'Githinji',  'Paul',     'KQ 100', 'NBO', 'LHR', '2026-12-25 09:30:00+03', '22F', 'confirmed'),
    ('BN7K1T', 'Wafula',    'Lucy',     'KQ 310', 'NBO', 'CDG', '2026-12-26 23:59:00+03', '8A',  'confirmed'),
    ('XC4H8L', 'Maina',     'George',   'KQ 532', 'NBO', 'DXB', '2026-12-21 14:45:00+03', '16E', 'delayed'),
    ('PV9D2R', 'Chebet',    'Nancy',    'KQ 762', 'NBO', 'JNB', '2026-12-27 07:15:00+03', '24A', 'confirmed')
on conflict (pnr, last_name) do nothing;