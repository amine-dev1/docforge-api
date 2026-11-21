import assert from 'node:assert/strict'
import { test } from 'node:test'
import { countries, countryByCode, countryForPhone, changePhoneCountry } from './countries.ts'

test('country choices have unique ISO codes and numeric dialing prefixes', () => {
  assert.ok(countries.length >= 249)
  assert.equal(countryByCode.size, countries.length)
  for (const country of countries) {
    assert.match(country.code, /^[A-Z]{2}$/)
    assert.match(country.dial, /^\d{1,4}$/)
    assert.ok(country.name)
  }
  assert.equal(countryByCode.get('MA').dial, '212')
  assert.equal(countryByCode.get('FR').dial, '33')
})

test('international paste detects country without modifying original values', () => {
  assert.equal(countryForPhone('+33 6 12 34 56 78'), 'FR')
  assert.equal(countryForPhone('0033 6 12 34 56 78'), 'FR')
  assert.equal(countryForPhone('+212 612345678'), 'MA')
  assert.equal(countryForPhone('+1 242 5551234'), 'BS')
  assert.equal(countryForPhone('+999 123456'), '')
})

test('shared calling codes retain an explicitly chosen country', () => {
  assert.equal(countryForPhone('+1 4165551234', 'CA'), 'CA')
  assert.equal(countryForPhone('+7 7011234567', 'KZ'), 'KZ')
  assert.equal(countryForPhone('+39 0669812345', 'VA'), 'VA')
  assert.equal(countryForPhone('', 'FR'), 'FR')
  assert.equal(countryForPhone('', 'invalid'), 'MA')
})

test('changing dialing prefix preserves national digits and extensions', () => {
  assert.equal(changePhoneCountry('+33 612345678', 'FR', 'MA'), '+212 612345678')
  assert.equal(changePhoneCountry('0033 612345678 ext 12', 'FR', 'MA'), '+212 612345678 ext 12')
  assert.equal(changePhoneCountry('+39 0612345678', 'IT', 'FR'), '+33 0612345678')
  assert.equal(changePhoneCountry('', 'MA', 'FR'), '+33 ')
  assert.equal(changePhoneCountry('0612345678', 'MA', 'FR'), '0612345678')
  assert.equal(changePhoneCountry('ancien numéro', 'MA', 'FR'), 'ancien numéro')
  assert.equal(changePhoneCountry('+212 612345678', 'MA', 'invalid'), '+212 612345678')
})
