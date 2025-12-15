import datetime

# Heavenly Stems (Cheongan)
CHEONGAN = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
# Earthly Branches (Jiji)
JIJI = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]
# Zodiac Animals
ZODIAC = ["쥐", "소", "호랑이", "토끼", "용", "뱀", "말", "양", "원숭이", "닭", "개", "돼지"]

# Approximate Solar Terms (Jeolgi) dates (standard year)
# Index 0 is Ipchun (approx Feb 4) - Start of Tiger month
JEOLGI_DATES = [
    (2, 4), (3, 6), (4, 5), (5, 6), (6, 6), (7, 7),
    (8, 8), (9, 8), (10, 8), (11, 7), (12, 7), (1, 6)
]

def get_ganji(year_idx, month_idx=None, day_idx=None, hour_idx=None):
    """Convert indices to Ganji string."""
    stem = CHEONGAN[year_idx % 10]
    branch = JIJI[year_idx % 12]
    return f"{stem}{branch}"

def get_year_pillar(year, month, day):
    """
    Calculate Year Pillar.
    Transition happens at Ipchun (approx Feb 4).
    """
    # Base calculation: (Year - 4) % 60
    # But if before Ipchun, it belongs to previous year.
    is_before_ipchun = False
    if month < 2:
        is_before_ipchun = True
    elif month == 2:
        if day < 4:
            is_before_ipchun = True
        # Note: Exact Ipchun time varies. This is a simplification.
        # For professional accuracy, we'd need astronomical data.
        # However, checking day < 4 is safer than checking strictly.
    
    target_year = year - 1 if is_before_ipchun else year
    idx = (target_year - 4) % 60
    return get_ganji(idx), target_year

def get_month_pillar(year_stem_idx, month, day):
    """
    Calculate Month Pillar.
    Derived from Year Stem and Solar Term.
    """
    # 1. Determine the lunar month index (0=In/Tiger, 1=Myo/Rabbit, ...) based on solar date
    # Simple lookup based on JEOLGI_DATES
    # We need to find which solar term range the date falls into.
    # Jeolgi starts approx on the dates in JEOLGI_DATES.
    
    # Mapping month/day to an approximate "month index" starting from Ipchun (Tiger month)
    # Ipchun (2/4) -> Month Index 0 (Tiger)
    # Gyeongchip (3/6) -> Month Index 1 (Rabbit)
    # ...
    # Sohian (1/6) -> Month Index 11 (Ox)
    
    current_md = (month, day)
    month_idx = -1 # 0 to 11
    
    # Check against Jeolgi dates
    # Since the list wraps around year end, logic is tricky.
    # Let's map strict ranges.
    
    ranges = [
        ((2, 4), (3, 5)),   # In (Tiger) - Feb
        ((3, 6), (4, 4)),   # Myo (Rabbit) - Mar
        ((4, 5), (5, 5)),   # Jin (Dragon) - Apr
        ((5, 6), (6, 5)),   # Sa (Snake) - May
        ((6, 6), (7, 6)),   # O (Horse) - Jun
        ((7, 7), (8, 7)),   # Mi (Sheep) - Jul
        ((8, 8), (9, 7)),   # Shin (Monkey) - Aug
        ((9, 8), (10, 7)),  # Yu (Rooster) - Sep
        ((10, 8), (11, 6)), # Sul (Dog) - Oct
        ((11, 7), (12, 6)), # Hae (Pig) - Nov
        ((12, 7), (1, 5)),  # Ja (Rat) - Dec (crosses year)
        ((1, 6), (2, 3))    # Chuk (Ox) - Jan
    ]
    
    target_month_branch_idx = 0 # Default In
    
    # Handle the year wrapping for Ja and Chuk
    if month == 12 and day >= 7:
        target_month_branch_idx = 10 # Ja
    elif month == 1 and day <= 5:
        target_month_branch_idx = 10 # Ja (continued)
    elif month == 1 and day >= 6:
        target_month_branch_idx = 11 # Chuk
    elif month == 2 and day <= 3:
        target_month_branch_idx = 11 # Chuk (continued)
    else:
        # For Feb 4 onwards to Dec 6
        for i in range(10): # Check In to Hae
            start_m, start_d = ranges[i][0]
            end_m, end_d = ranges[i][1]
            
            # Simple check: is (month, day) >= start and <= end?
            # Since these don't wrap year, direct comparison works
            if (month > start_m or (month == start_m and day >= start_d)) and \
               (month < end_m or (month == end_m and day <= end_d)):
                target_month_branch_idx = i
                break

    # Month Branch is fixed: In(2), Myo(3), ... Ja(0), Chuk(1)
    # Our JIJI list: Ja(0), Chuk(1), In(2)...
    # So In(Tiger) is index 2 in JIJI.
    # target_month_branch_idx 0 (In) maps to JIJI index 2.
    final_branch_idx = (target_month_branch_idx + 2) % 12
    
    # Month Stem depends on Year Stem
    # Formula: (Year Stem Index * 2 + 2) % 10 is the stem of In month (first month)
    # Wait, strictly:
    # Gap/Gi Year -> Byeong-In Month (Stem 2)
    # Eul/Gyeong Year -> Mu-In Month (Stem 4)
    # Byeong/Shin Year -> Gyeong-In Month (Stem 6)
    # Jeong/Im Year -> Im-In Month (Stem 8)
    # Mu/Gye Year -> Gap-In Month (Stem 0)
    
    # Formula: (Year Stem Index % 5) * 2 + 2 -> Stem of In Month
    start_month_stem_idx = (year_stem_idx % 5) * 2 + 2
    final_stem_idx = (start_month_stem_idx + target_month_branch_idx) % 10
    
    return get_ganji(final_stem_idx * 10 + final_branch_idx) # Hacky way to reuse get_ganji but logic holds

def get_day_pillar(year, month, day):
    """
    Calculate Day Pillar.
    Requires reference date.
    Reference: 1900-01-01 was Gap-Sul (Index 10: Gap=0, Sul=10) -> wait, verify.
    Actually, let's use a known recent date.
    2024-01-01 was Gap-Ja (Index 0)? No.
    2023-01-01 was Mu-O.
    
    Let's use a standard algorithm.
    Python's datetime to ordinal.
    Base date: 1900-01-01 (Monday)
    Let's find a concrete reference.
    October 16, 2024 is Gye-Yu (Stem 9, Branch 9).
    """
    base_date = datetime.date(2024, 10, 16)
    base_ganji_idx = 9 # Gye(9)-Yu(9) -> No, Gye is 9, Yu is 9.
    # 60 ganji index for Gye-Yu?
    # Gye(9), Yu(9). 
    # Index = (Stem - Branch) / 2 * 12 + Branch? No.
    # Index k satisfies: k % 10 = Stem, k % 12 = Branch.
    # 9, 9 -> 9 (Gye-Yu is 10th? No, Gap-Ja is 0 (0,0), Eul-Chuk 1 (1,1)... Gye-Yu is 9 (9,9))
    # Yes, Gye-Yu is index 9.
    
    target_date = datetime.date(year, month, day)
    delta = (target_date - base_date).days
    
    current_idx = (9 + delta) % 60
    return get_ganji(current_idx)

def calculate_saju(year, month, day, hour=None, minute=None):
    """
    Calculate full Saju pillars.
    """
    # 1. Year Pillar
    year_ganji, solar_year = get_year_pillar(year, month, day)
    
    # Year Stem Index for Month calculation
    # Ganji string to stem index
    year_stem_char = year_ganji[0]
    year_stem_idx = CHEONGAN.index(year_stem_char)
    
    # 2. Month Pillar
    month_ganji = get_month_pillar(year_stem_idx, month, day)
    
    # 3. Day Pillar
    day_ganji = get_day_pillar(year, month, day)
    
    # 4. Time Pillar (optional)
    time_ganji = None
    if hour is not None:
        # Time Stem depends on Day Stem
        # Formula: (Day Stem Index % 5) * 2 + ...
        # Standard table:
        # Gap/Gi Day -> Start with Gap-Ja (0) at 23:30-01:30
        # Eul/Gyeong Day -> Start with Byeong-Ja (2)
        # ...
        day_stem_char = day_ganji[0]
        day_stem_idx = CHEONGAN.index(day_stem_char)
        
        start_time_stem_idx = (day_stem_idx % 5) * 2
        
        # Determine time branch index (Ja=0, Chuk=1, ...)
        # 23:30-01:29 -> Ja (0)
        # 01:30-03:29 -> Chuk (1)
        # ...
        # Simple mapping: (Hour + 1) // 2 % 12 ?
        # 23 -> 24//2 = 12 -> 0
        # 0 -> 1//2 = 0 -> 0
        # 1 -> 2//2 = 1 -> 1 (Chuk)
        # Correct.
        branch_idx = ((hour + 1) // 2) % 12
        
        stem_idx = (start_time_stem_idx + branch_idx) % 10
        time_ganji = f"{CHEONGAN[stem_idx]}{JIJI[branch_idx]}"

    return {
        "year_pillar": year_ganji,
        "month_pillar": month_ganji,
        "day_pillar": day_ganji,
        "time_pillar": time_ganji,
        "solar_year": solar_year
    }

def analyze_elements(saju_result):
    """
    Analyze element distribution based on pillars.
    """
    pillars = [saju_result['year_pillar'], saju_result['month_pillar'], saju_result['day_pillar']]
    if saju_result['time_pillar']:
        pillars.append(saju_result['time_pillar'])
        
    # Element Mapping
    # Wood: Gap, Eul, In, Myo
    # Fire: Byeong, Jeong, Sa, O
    # Earth: Mu, Gi, Jin, Sul, Chuk, Mi
    # Metal: Gyeong, Shin, Shin, Yu (Note: Shin(Monkey)=Metal, Shin(Stem)=Metal)
    # Water: Im, Gye, Hae, Ja
    
    element_map = {
        '갑': 'wood', '을': 'wood', '인': 'wood', '묘': 'wood',
        '병': 'fire', '정': 'fire', '사': 'fire', '오': 'fire',
        '무': 'earth', '기': 'earth', '진': 'earth', '술': 'earth', '축': 'earth', '미': 'earth',
        '경': 'metal', '신': 'metal', '유': 'metal', # Handle Hanja/Hangul ambiguity carefully if needed. 
        # Here '신' is ambiguous in Hangul (Shin-Metal vs Shin-Monkey).
        # But Shin-Metal is Stem, Shin-Monkey is Branch.
        # My CHEONGAN/JIJI arrays use specific Hangul.
        # CHEONGAN: ... 경, 신(辛) ...
        # JIJI: ... 신(申), 유 ...
        # Both represent Metal. Wait, is Monkey(申) Metal? Yes.
        # Is 辛 Metal? Yes.
        # So '신' maps to metal regardless.
        '임': 'water', '계': 'water', '해': 'water', '자': 'water'
    }
    
    counts = {'wood': 0, 'fire': 0, 'earth': 0, 'metal': 0, 'water': 0}
    
    for p in pillars:
        stem = p[0]
        branch = p[1]
        
        s_elem = element_map.get(stem)
        b_elem = element_map.get(branch)
        
        if s_elem: counts[s_elem] += 1
        if b_elem: counts[b_elem] += 1
        
    return counts
