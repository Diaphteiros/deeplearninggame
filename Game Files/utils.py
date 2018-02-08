# returns whether z can be interpreted as an integer
def isInt(z):
	try:
		int(z)
		return True
	except ValueError:
		return False


# returns whether z can be interpreted as a float
def isFloat(z):
	try:
		float(z)
		return True
	except ValueError:
		return False


# converts z to an integer or float if possible and returns it
def convertToNumberIfPossible(z):
	if isInt(z):
		return int(z)
	elif isFloat(z):
		return float(z)
	else:
		return z


# returns whether z can be interpreted as either integer or float
def isNumber(z):
	return isInt(z) or isFloat(z)
