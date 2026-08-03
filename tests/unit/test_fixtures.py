def test_fixtures_build_a_tenant(customer_analyst, customer_org):
    assert customer_analyst.org_id == customer_org.id
    assert customer_analyst.is_active is True


def test_truncation_resets_between_tests(make_org):
    org = make_org()
    assert org.id == 1