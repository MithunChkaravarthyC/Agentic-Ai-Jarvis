import asyncio, sys
sys.path.insert(0, '.')

async def test():
    from backend.agents.jarvis_orchestrator import jarvis_orchestrator

    tests = [
        ('open up kiro fast', 'app_launched'),
        ('open note pad in my latop', 'app_launched'),
        ('Open Calculator', 'app_launched'),
        ('Swiggy Biryani', 'swiggy_awaiting_approval'),
        ('order pizza', 'swiggy_awaiting_approval'),
        ('Book Flight from Chennai to Delhi', 'flight_awaiting_approval'),
    ]

    all_passed = True
    for msg, expected_type in tests:
        r = await jarvis_orchestrator.handle_user_input(msg)
        status = 'PASS' if r['type'] == expected_type else 'FAIL'
        if status == 'FAIL': all_passed = False
        print(f'  [{status}] "{msg}" => {r["type"]} | {r["reply"][:75]}')

    print()
    print('ALL PASSED!' if all_passed else 'SOME TESTS FAILED')

asyncio.run(test())
