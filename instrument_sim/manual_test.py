from driver.signal_generator import SignalGeneratorDriver

gen = SignalGeneratorDriver()

print("IDN:", gen.get_idn())
gen.set_frequency(2_500_000_000)
print("Frequency:", gen.get_frequency())
gen.set_power(999)  # invalid — out of range
print("Error after bad power:", gen.get_last_error())
gen.set_output(True)
print("Output on:", gen.get_output())

gen.close()