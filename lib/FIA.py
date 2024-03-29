"""Utilities for Fixed Income Analytics course"""

"""
Copyright (c) 2020 Cameron R. Connell

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


import math

HASNUMPY = 1
try:
    import numpy as np
except ImportError:
    print("Plotting functions require Numpy")
    print("Plotting functions inoperable")
    HASNUMPY = 0

HASMATPLOTLIB = 1
try:
    import matplotlib.pyplot as plt
except ImportError:
    print("Plotting functions require Matplotlib")
    print("Plotting functions inoperable")
    HASMATPLOTLIB = 0


# Interpolator classes needed for yield curves
class abstract_interpolator:
    def __init__(self, xvals=[], yvals=[]):
        # Check that xvalues and yvalues have same length
        self.length = len(xvals)
        if self.length != len(yvals):
            print("Warning: abscissae and ordinates have different length")

        # Check that xvalues are sorted
        temp = xvals.copy()
        temp.sort()
        if temp != xvals:
            print("Warning: xvalues out of order")

        self.abscissae = xvals.copy()
        self.ordinates = yvals.copy()

    def extend(self, xval, yval):
        self.abscissae.append(xval)
        self.abscissae.sort()
        index = self.abscissae.index(xval)
        self.ordinates.insert(index, yval)
        self.length += 1

    def get_abscissae(self):
        return self.abscissae

    def get_ordinates(self):
        return self.ordinates

    def __len__(self):
        return self.length


class pwlinear_interpolator(abstract_interpolator):
    def eval(self, x):
        if self.length == 0:
            print("Empty interpolator")
            return

        boolvect = [(x <= abscissa) for abscissa in self.abscissae]
        try:
            index = boolvect.index(True)
        except ValueError:
            print("Warning: extrapolating outside range")
            return self.ordinates[self.length - 1]

        if index == 0:
            return self.ordinates[0]
        else:
            alpha = (x - self.abscissae[index - 1]) / (
                self.abscissae[index] - self.abscissae[index - 1]
            )
            return (1.0 - alpha) * self.ordinates[index - 1] + alpha * self.ordinates[
                index
            ]

    def delta(self, x, bump_index):  # Delta wrt benchmarks
        if self.length == 0:
            print("Empty interpolator")
            return

        if bump_index >= self.length:
            print("Index out of range")
            return

        if self.length == 1:
            return 1.0

        boolvect = [(x <= abscissa) for abscissa in self.abscissae]
        try:
            index = boolvect.index(True)
        except ValueError:
            print("Warning: extrapolating outside range")
            return_val = 1.0 if bump_index == (self.length - 1) else 0.0
            return return_val

        if bump_index < index - 1 or bump_index > index:
            return 0.0

        alpha = (x - self.abscissae[index - 1]) / (
            self.abscissae[index] - self.abscissae[index - 1]
        )
        if bump_index == (index - 1):
            return 1.0 - alpha
        if bump_index == index:
            return alpha

    def copy(self):
        new_interpolator = pwlinear_interpolator(self.abscissae, self.ordinates)
        return new_interpolator


class catmull_rom_interpolator(abstract_interpolator):
    def __init__(self, xvals=[], yvals=[]):
        abstract_interpolator.__init__(self, xvals, yvals)

        A = [0] * 4
        self.coefficients = []

        beta = (self.abscissae[1] - self.abscissae[0]) / (
            self.abscissae[2] - self.abscissae[0]
        )

        A[0] = (
            (1.0 - beta) * self.ordinates[0]
            - self.ordinates[1]
            + beta * self.ordinates[2]
        )
        A[1] = (
            (-1.0 + beta) * self.ordinates[0]
            + self.ordinates[1]
            - beta * self.ordinates[2]
        )
        A[2] = -self.ordinates[0] + self.ordinates[1]
        A[3] = self.ordinates[0]

        self.coefficients.append(A.copy())

        for i in range(1, self.length - 2):
            alpha = (self.abscissae[i + 1] - self.abscissae[i]) / (
                self.abscissae[i + 1] - self.abscissae[i - 1]
            )
            beta = (self.abscissae[i + 1] - self.abscissae[i]) / (
                self.abscissae[i + 2] - self.abscissae[i]
            )

            A[0] = (
                -alpha * self.ordinates[i - 1]
                + (2.0 - beta) * self.ordinates[i]
                + (-2.0 + alpha) * self.ordinates[i + 1]
                + beta * self.ordinates[i + 2]
            )
            A[1] = (
                2.0 * alpha * self.ordinates[i - 1]
                + (beta - 3.0) * self.ordinates[i]
                + (3.0 - 2.0 * alpha) * self.ordinates[i + 1]
                - beta * self.ordinates[i + 2]
            )
            A[2] = -alpha * self.ordinates[i - 1] + alpha * self.ordinates[i + 1]
            A[3] = self.ordinates[i]

            self.coefficients.append(A.copy())

        alpha = (self.abscissae[self.length - 1] - self.abscissae[self.length - 2]) / (
            self.abscissae[self.length - 1] - self.abscissae[self.length - 3]
        )

        A[0] = (
            -alpha * self.ordinates[self.length - 3]
            + self.ordinates[self.length - 2]
            + (-1.0 + alpha) * self.ordinates[self.length - 1]
        )
        A[1] = (
            2.0 * alpha * self.ordinates[self.length - 3]
            - 2.0 * self.ordinates[self.length - 2]
            + (2.0 - 2.0 * alpha) * self.ordinates[self.length - 1]
        )
        A[2] = (
            -alpha * self.ordinates[self.length - 3]
            + alpha * self.ordinates[self.length - 1]
        )
        A[3] = self.ordinates[self.length - 2]

        self.coefficients.append(A.copy())

    def eval(self, x):
        if self.length == 0:
            print("Empty interpolator")
            return

        boolvect = [(x <= abscissa) for abscissa in self.abscissae]
        try:
            index = boolvect.index(True)
        except ValueError:
            print("Warning: extrapolating outside range")
            return self.ordinates[self.length - 1]

        if index == 0:
            return self.ordinates[0]
        else:
            delta = (x - self.abscissae[index - 1]) / (
                self.abscissae[index] - self.abscissae[index - 1]
            )
            return (
                self.coefficients[index - 1][0] * delta**3
                + self.coefficients[index - 1][1] * delta**2
                + self.coefficients[index - 1][2] * delta
                + self.coefficients[index - 1][3]
            )

    def delta(self, x, bump_index):
        pass

    def copy(self):
        new_interpolator = catmull_rom_interpolator(self.abscissae, self.ordinates)
        return new_interpolator


class natural_spline_interpolator(abstract_interpolator):
    def __init__(self, xvals=[], yvals=[]):
        abstract_interpolator.__init__(self, xvals, yvals)

        lhs_matrix = np.zeros([self.length, self.length])

        lhs_matrix[0, 0] = 1.0

        for i in range(1, self.length - 1):
            lhs_matrix[i, i - 1] = (self.abscissae[i] - self.abscissae[i - 1]) / 6.0
            lhs_matrix[i, i] = (self.abscissae[i + 1] - self.abscissae[i - 1]) / 3.0
            lhs_matrix[i, i + 1] = (self.abscissae[i + 1] - self.abscissae[i]) / 6.0

        lhs_matrix[self.length - 1, self.length - 1] = 1.0

        rhs = np.zeros([self.length])

        for i in range(1, self.length - 1):
            rhs[i] = (self.ordinates[i + 1] - self.ordinates[i]) / (
                self.abscissae[i + 1] - self.abscissae[i]
            ) - (self.ordinates[i] - self.ordinates[i - 1]) / (
                self.abscissae[i] - self.abscissae[i - 1]
            )

        self.fprimeprime = np.linalg.solve(lhs_matrix, rhs)

    def eval(self, x):
        if self.length == 0:
            print("Empty interpolator")
            return

        boolvect = [(x <= abscissa) for abscissa in self.abscissae]
        try:
            index = boolvect.index(True)
        except ValueError:
            print("Warning: extrapolating outside range")
            return self.ordinates[self.length - 1]

        if index == 0:
            return self.ordinates[0]
        else:
            xplus = self.abscissae[index] - x
            xminus = x - self.abscissae[index - 1]
            h = self.abscissae[index] - self.abscissae[index - 1]
            return (
                self.fprimeprime[index - 1] * xplus**3 / h / 6.0
                + self.fprimeprime[index] * xminus**3 / h / 6.0
                + (
                    self.ordinates[index - 1] / h
                    - h * self.fprimeprime[index - 1] / 6.0
                )
                * xplus
                + (self.ordinates[index] / h - h * self.fprimeprime[index] / 6.0)
                * xminus
            )

    def delta(self, x, bump_index):
        pass

    def copy(self):
        new_interpolator = natural_spline_interpolator(self.abscissae, self.ordinates)
        return new_interpolator


# Newton solver for extending curve by 1 tenor
def solver(interpolator, bond):
    tolerance = 0.000001

    dates = bond.get_dates()
    coupons = bond.get_cashflows()
    maturity = bond.get_maturity()

    try:
        price = bond.get_price()
        if price == None:
            raise ValueError("No bond price available")
    except ValueError:
        raise

    def F(eta):
        _interpolator = interpolator.copy()
        _interpolator.extend(maturity, eta)

        sum = -price

        for i in range(len(dates)):
            sum += math.exp(-_interpolator.eval(dates[i]) * dates[i]) * coupons[i]

        return sum

    def Fprime(eta):
        _interpolator = interpolator.copy()
        _interpolator.extend(maturity, eta)

        max_index = len(_interpolator) - 1

        sum = 0.0

        for i in range(len(dates)):
            sum += (
                _interpolator.delta(dates[i], max_index)
                * dates[i]
                * math.exp(-_interpolator.eval(dates[i]) * dates[i])
                * coupons[i]
            )

        return -sum

    old_eta = 0.0
    new_eta = old_eta - F(old_eta) / Fprime(old_eta)

    while abs(new_eta - old_eta) > tolerance:
        old_eta = new_eta
        new_eta = old_eta - F(old_eta) / Fprime(old_eta)

    return new_eta


# Class for yield curves
class curve:
    """
    Class for yield curves

    Attributes
    ----------
    tenors: list
        The tenors of the yield curve
    rates: list
        The spot rates (continuously compunded) that define the rate.  Must have the same length
        as tenors
    length: integer
        The length of the tenor and rate vectors
    interpolator: interpolator object
        The interpolator object responsible for interpolating the defining rates in the rates
        vector
    """

    def __init__(self):
        self.tenors = []
        self.rates = []
        self.length = 0
        self.interpolator = None

    def build_from_rates(self, dates, rates, method="pwlinear"):
        if self.length > 0:
            print("Curve is already built")
            return

        if len(dates) != len(rates):
            print("Rate and tenor vectors of unequal lengths")
            return

        self.tenors = dates.copy()
        self.rates = rates.copy()
        self.length = len(dates)

        if method == "pwlinear":
            self.interpolator = pwlinear_interpolator(dates, rates)
        elif method == "hermite":
            self.interpolator = catmull_rom_interpolator(dates, rates)
        elif method == "natural":
            self.interpolator = natural_spline_interpolator(dates, rates)
        else:
            print(
                "Unrecognized interpolation method.  Defaulting to piecewise linear interpolation"
            )
            self.interpolator = pwlinear_interpolator(dates, rates)

    def build_from_bonds(self, bond_list, method="pwlinear"):
        if self.length > 0:
            print("Curve is already built")
            return

        num_of_bonds = len(bond_list)

        def get_max_date(bond):
            return bond.get_maturity()

        bond_list.sort(key=get_max_date)

        if method == "pwlinear":
            self.interpolator = pwlinear_interpolator()
        else:
            print(
                "Only piecewise linear interpolation is available for building curve from bond prices"
            )
            print("Reverting to piecewise linear interpolation")
            self.interpolator = pwlinear_interpolator()

        for i in range(num_of_bonds):
            new_rate = solver(self.interpolator, bond_list[i])
            self.interpolator.extend(bond_list[i].get_maturity(), new_rate)
            self.tenors.append(bond_list[i].get_maturity())
            self.rates.append(new_rate)
            self.length += 1

    def build_nelson_siegel(self, dates, rates, tau=2.5):
        if self.length > 0:
            print("Curve is already built")
            return

        if len(dates) != len(rates):
            print("Rate and tenor vectors of unequal lengths")
            return

        self.tenors = dates.copy()
        self.rates = rates.copy()
        self.length = len(dates)

        ordinates = np.array(rates)

        loadings = np.ones([self.length, self.length, self.length])
        for i in range(self.length):
            loadings[i, 1] = (1.0 - exp(-tau * dates[i])) / tau / dates[i]
            loadings[i, 2] = (1.0 - exp(-tau * dates[i])) / tau / dates[i] - exp(
                -tau * dates[i]
            )

        beta = np.linalg.lstsq(loadings, ordinates)

    def get_rates(self):
        """
        Returns the rates attribute

        Parameters
        ----------
        None

        Returns
        -------
        list
            List of defining interest rates in the rates attribute
        """
        rates = []
        for rate in self.rates:
            rates.append(rate * 100)
        return rates

    def get_tenors(self):
        """
        Returns the tenors attribute

        Parameters
        ----------
        None

        Returns
        -------
        list
            List of defining interest rates in the rates attribute
        """
        return self.tenors

    def shift(self, delta):
        """
        Shifts all interest rates in the rates attribute by the same amount

        Parameters
        ----------
        delta: float
            The quantity (percentage) to shift interest rates

        Returns
        -------
        curve
            A new curve object with the shifted rates
        """
        delta /= 100
        new_rates = []
        for i in range(self.length):
            new_rates.append(self.rates[i] + delta)
        new_curve = curve()
        new_curve.build_from_rates(rates=new_rates, dates=self.tenors)
        return new_curve

    def bump(self, delta, index):
        """
        Shifts one benchmark rate from the rates list.

        Parameters
        ----------
        delta: float
            The quantity (percentage) to shift the chosen interest rate.
        index: int
            The index of the rate to shift.

        Returns
        -------
            A new curve object with the bumped rate
        """

        delta /= 100
        new_rates = self.rates.copy()
        new_rates[index] += delta
        new_curve = curve()
        new_curve.build_from_rates(rates=new_rates, dates=self.tenors)
        return new_curve

    def get_yield(self, time):
        """
        Evaluates and returns the continuously compounded spot rate for a given tenor.

        Parameters
        ----------
        time: float
            The tenor at which to evaluate the spot rate.

        Returns
        -------
        double
            The continuously compounded spot rate for the chosen tenor.
        """
        return 100 * self.interpolator.eval(time)

    def discount_factor(self, time):
        """
        Evaluates and returns the discount factor for the given tenor.

        Parameters
        ----------
        time: float
            The tenor at which to evaluate the discount factor.

        Returns
        -------
        float
            The implied discount factor at the chosen tenor.
        """
        return math.exp(-self.interpolator.eval(time) * time)

    def ddr(self, time, compounding=1):
        if compounding == 0:
            exponent = 1.0
        else:
            exponent = 1.0 + 1.0 / time / compounding

        return -time * self.discount_factor(time) ** exponent

    def ddr2(self, time, compounding=1):
        if compounding == 0:
            return time**2 * self.discount_factor(time)
        else:
            exponent = 1.0 + 2.0 / time / compounding

        return (
            time * (time + 1.0 / compounding) * self.discount_factor(time) ** exponent
        )

    def spot_rate(self, time, compounding=1):
        """
        Evaluates and returns the spot rate for a given tenor and compounding convention

        Parameters
        ----------
        time: float
            The tenor of the desired spot rate.
        compounding: int
            The desired compounding convention (default is 1 => annual compounding).

        Returns
        -------
        float
            The requested spot rate.
        """

        if compounding == 0:
            return 100 * (1.0 / self.discount_factor(time) - 1.0) / time

        if compounding > 0:
            df = self.discount_factor(time)
            return 100 * compounding * (df ** (-1.0 / compounding / time) - 1.0)

        print("Invalid compounding convention")
        return

    def forward_rate(self, start, maturity, compounding=1):
        """
        Evaluates and returns the implied forward rate for a given start, maturity, and
        compounding covention.

        Parameters
        ----------
        start: float
            The start date for the future loan period.
        maturity: float
            The end date for the future loan period.
        compounding: int
            The desired compounding convention (default is 1 => annual compounding).

        Returns
        float
            The requested forward rate.
        """
        if not (maturity > start):
            print("Maturity date must be later than start date")
            return

        if compounding == 0:
            y1 = self.interpolator.eval(start)
            y2 = self.interpolator.eval(maturity)
            return 100 * (maturity * y2 - start * y1) / (maturity - start)

        if compounding > 0:
            df1 = self.discount_factor(start)
            df2 = self.discount_factor(maturity)
            return (
                100
                * compounding
                * ((df1 / df2) ** (1.0 / compounding / (maturity - start)) - 1.0)
            )

        print("Invalid compounding convention")
        return

    def copy(self):
        """
        Creates a deep copy of the curve object.

        Parameters
        ----------
        None

        Returns
        -------
        list
            List of defining interest rates in the rates attribute
        """
        new_curve = curve()
        new_curve.build_from_rates(rates=self.rates, dates=self.tenors)
        return new_curve

    def __len__(self):
        return self.length

    def plot_yields(self, compounding=0, max_tenor=0):
        """
        Displays a plot of the full (with interpolated values) curve of continuously compounded
        rates.  Requires Matplotlib.

        Parameters
        ----------
        compounding: int
            compounding convention of rates displayed (defaults to continuous compounding)
        max_tenor: float
            Right limit of the displayed graph (defaults to the maximum stored tenor).

        Returns
        -------
        None.
        """
        if not HASMATPLOTLIB:
            print("Plotting functions require Matplotlib")
            return

        if max_tenor <= 0:
            max_tenor = max(self.tenors)

        fig = plt.figure()
        ax = fig.subplots()

        t = np.arange(0.1, max_tenor, 0.1)

        y = []
        for tenor in t:
            if compounding == 0:
                yld = self.get_yield(tenor)
            else:
                yld = self.spot_rate(tenor, compounding)
            y.append(yld)

        yields = np.array(y)

        ax.ticklabel_format(useOffset=False)
        ax.plot(t, yields)
        minyield = yields.min()
        maxyield = yields.max()
        ax.set_ylim([minyield - 1, maxyield + 1])

        ax.set(xlabel="tenor", ylabel="yield", title="Yields")

        plt.show(block=False)

    def plot_discount_factors(self, max_tenor=0):
        """
        Displays a plot of the implied discount factors.  Requires Matplotlib.

        Parameters
        ----------
        max_tenor: float
            Right limit of the displayed graph (defaults to the maximum stored tenor).

        Returns
        -------
        None.
        """
        if not HASMATPLOTLIB:
            print("Plotting functions require Matplotlib")
            return

        if max_tenor <= 0:
            max_tenor = max(self.tenors)

        fig, ax = plt.subplots()

        t = np.arange(0.0, max_tenor, 0.1)

        d = []
        for tenor in t:
            yld = self.discount_factor(tenor)
            d.append(yld)

        dfs = np.array(d)

        ax.plot(t, dfs)

        ax.set(xlabel="tenor", ylabel="discount factor", title="Discount Factors")

        plt.show(block=False)

    def plot_forwards(self, start, maturity=0, compounding=1):
        """
        Displays a plot of the implied forward curve for a specified start date and maturity.
        (Requires Matplotlib).

        Parameters
        ----------
        start: float
            Forward start date.
        maturity: float
            Longest maturity to plot.

        Returns
        -------
        None.
        """
        if not HASMATPLOTLIB:
            print("Plotting functions require Matplotlib")
            return

        if maturity <= 0:
            maturity = max(self.tenors)

        if maturity <= start:
            print("Maturity must follow start")
            return

        fig, ax = plt.subplots()

        t = np.arange(start + 0.1, maturity, 0.1)

        f = []
        for tenor in t:
            rate = self.forward_rate(start, tenor, compounding)
            f.append(rate)

        forward_rates = np.array(f)

        ax.plot(t, forward_rates)

        ax.set(xlabel="tenor", ylabel="forward rate", title="Forward Rates")

        plt.show(block=False)


# Classes for bonds
class abstract_bond:
    def __init__(self, rates=[], times=[], price=None):
        self.coupons = rates
        self.dates = times
        self.length = len(rates)
        self.market_price = price

    def build(self, rates, dates):
        if len(rates) == 0:
            print("No coupons given")
            return

        if len(rates) != len(dates):
            print("Coupon and tenor vectors incommensurate")
            return

        self.coupons = rates
        self.dates = dates
        self.length = len(rates)

    def get_cashflows(self):
        """
        Returns the list of stored coupons,

        Parameters
        ----------
        None,

        Returns
        -------
        list
            The coupons list attribute.
        """
        return self.coupons

    def get_dates(self):
        """
        Returns the stored list of payment dates.

        Parameters
        ----------
        None.

        Returns
        -------
        list
            The dates list attribute.
        """
        return self.dates

    def get_maturity(self):
        """
        Returns the maturity of the bond, the longest date in the dates attribute.

        Parameters
        ----------
        None

        Returns
        -------
        list
            The maximum date of the dates list attribute.
        """
        return max(self.dates)

    def get_price(self):
        """
        Returns the stored market price of the bond.

        Parameters
        ----------
        None.

        Returns
        -------
        float
            The stored price of the bond (the market_price attribute).
        """
        if self.market_price == None:
            print("No price available")
            return
        else:
            return self.market_price

    def set_price(self, price):
        """
        Sets the stored market price

        Parameters
        ----------
        price: float
            Specified market price for the bond.

        Returns
        -------
        None.
        """
        self.market_price = price

    def __len__(self):
        return self.length

    def plot_payments(self):
        """
        Displays a plot of the bond payments.

        Parameters
        ----------
        None.

        Returns
        -------
        None.
        """
        if not HASMATPLOTLIB:
            print("Plotting functions require Matplotlib")
            return

        fig, ax = plt.subplots()

        ax.bar(self.dates, self.coupons, width=0.2)
        ax.set_xlabel("payment dates (years)")
        ax.set_ylabel("payments")
        ax.set_title("Coupon Bond Payments")
        ax.set_xlim(0.0)

        plt.show(block=False)


class relative_bond(abstract_bond):
    def price(self, curve, date=0, compounding=0):
        """
        Prices the bond with a specified yield curve.

        Parameters
        ----------
        curve: curve
            The first positional argument must be either a
            curve object or a number.  If it is a number,
            it is interpreted as a yield to maturity.
        date: float
            The date on which to price the bond (defaults to 0)
        compounding: integer
            The compounding convention if the bond is being
            priced with a yield (defaults to continuous
            compounding)
        Returns
        -------
        float
            The calculated bond price.
        """
        if type(curve) == int or type(curve) == float:
            if compounding > 0:
                y = compounding * math.log(1 + 0.01 * curve / compounding)
            else:
                y = 0.01 * curve
            pv = 0.0
            for i in range(self.length):
                if self.dates[i] < date:
                    continue
                pv += math.exp(-y * (self.dates[i] - date)) * self.coupons[i]

            return pv

        pv = 0.0
        for i in range(self.length):
            if self.dates[i] < date:
                continue
            try:
                pv += curve.discount_factor(self.dates[i] - date) * self.coupons[i]
            except AttributeError:
                print("argument must be either a number or a curve object")
                print("no price calculated")
                return None

        return pv

    def duration(self, curve, date=0, compounding=1):
        """
        Calculates the duration of the bond with the inputted yield
        curve.

        Parameters
        ----------
        curve: curve
            The curve object to use to compute the duration.
        date: float
            The date on which to calculate the duration (defaults to 0)
        compounding: integer
            The compounding convention to use to calculate the
            duration (defaults to annual compounding).
        Returns
        -------
        float
            The calculated duration.
        """

        sum = 0.0
        for i in range(self.length):
            if self.dates[i] < date:
                continue
            exponent = 1.0 + 1.0 / self.dates[i]
            sum += curve.ddr(self.dates[i] - date, compounding) * self.coupons[i]

        return -sum / self.price(curve, date)

    def dollar(self, curve, date=0, compounding=1):
        """
        Calculates the dollar duration of the bond with the inputted
        yield curve.

        Parameters
        ----------
        curve: curve
            The curve object to use to compute the dollar duration.
        date: float
            The date on which to calculate the dollar duration (defaults to 0)
        compounding: integer
            The compounding convention to use to calculate the
            dollar duration (defaults to annual compounding).

        Returns
        -------
        float
            The calculated dollar duration.
        """

        sum = 0.0
        for i in range(self.length):
            if self.dates[i] < date:
                continue
            exponent = 1.0 + 1.0 / self.dates[i]
            sum += curve.ddr(self.dates[i] - date, compounding) * self.coupons[i]

        return -sum

    def macaulay(self, curve, date=0):
        """
        Calculates the Macaulay duration of the bond with the inputted
        yield curve.

        Parameters
        ----------
        curve: curve
            The curve object to use to compute the Macaulay duration.
        date: float
            The date on which to calculate the Macaulay duration (defaults to 0)

        Returns
        -------
        float
            The calculated Macaulay duration.
        """

        sum = 0.0
        for i in range(self.length):
            if self.dates[i] < date:
                continue
            sum += (
                (self.dates[i] - date)
                * curve.discount_factor(self.dates[i] - date)
                * self.coupons[i]
            )

        return sum / self.price(curve, date)

    def dispersion(self, curve, date=0):
        """
        Calculates the dispersion of the bond with the inputted yield
        curve.

        Parameters
        ----------
        curve: curve
            The curve object to use to compute the dispersion.
        date: float
            The date on which to calculate the dispersion (defaults to 0).

        Returns
        -------
        float
            The calculated dispersion.
        """

        sum = 0.0
        duration = self.macaulay(curve, date)
        for i in range(self.length):
            if self.dates[i] < date:
                continue
            sum += (
                (self.dates[i] - date - duration) ** 2
                * curve.discount_factor(self.dates[i] - date)
                * self.coupons[i]
            )

        return sum / self.price(curve, date)

    def convexity(self, curve, date=0, compounding=1):
        """
        Calculates the convexity of the bond with the inputted yield
        curve.

        Parameters
        ----------
        curve: curve
            The curve object to use to compute the convexity.
        date: float
            The date on which to calculate the convexity (defaults to 0)
        compounding: integer
            The compounding convention to use to calculate the
            convexity (defaults to annual compounding).

        Returns
        -------
        float
            The calculated convexity.
        """

        sum = 0.0
        for i in range(self.length):
            if self.dates[i] < date:
                continue
            exponent = 1.0 + 1.0 / self.dates[i]
            sum += curve.ddr2(self.dates[i] - date, compounding) * self.coupons[i]

        return sum / self.price(curve, date)

    def dollar_convexity(self, curve, date=0, compounding=1):
        """
        Calculates the dollar convexity of the bond with the inputted
        yield curve.

        Parameters
        ----------
        curve: curve
            The curve object to use to compute the dollar convexity.
        date: float
            The date on which to calculate the dollar convexity (defaults to 0)
        compounding: integer
            The compounding convention to use to calculate the
            dollar convexity (defaults to annual compounding).

        Returns
        -------
        float
            The calculated dollar convexity.
        """

        sum = 0.0
        for i in range(self.length):
            if self.dates[i] < date:
                continue
            exponent = 1.0 + 1.0 / self.dates[i]
            sum += curve.ddr2(self.dates[i] - date, compounding) * self.coupons[i]

        return sum

    def YTM(self, price, **kwargs):
        """
        Calculates and returns the yield-to-maturity for a specified bond price.

        Parameters
        ----------
        price: float
            Specified bond price for which the yield-to-maturity will be calculated
            (defaults to the stored market price).
        Keyword Arguments:
            compounding: int
                If given, specifies the compounding convention of the yield
                that will be returned.

        Returns
        -------
        float
            The calculated yield-to-maturity.
        """

        if price == None:
            price = self.market_price

        if price == None:
            print("No price available")
            return

        if "compounding" in kwargs:
            compounding = kwargs["compounding"]
        else:
            compounding = None

        if self.length == 1:
            cts = -100 * math.log(price / self.coupons[0]) / self.dates[0]
            if compounding == None:
                return cts
            else:
                return 100 * compounding * (math.exp(cts / 100 / compounding) - 1)

        if compounding == None:
            compounding = round(1 / (self.dates[1] - self.dates[0]))

        tolerance = 0.000001

        def F(y):
            sum = 0.0
            for i in range(self.length):
                sum += self.coupons[i] * math.exp(-y * self.dates[i])

            return sum - price

        def Fprime(y):
            sum = 0.0
            for i in range(self.length):
                sum += self.dates[i] * self.coupons[i] * math.exp(-y * self.dates[i])

            return -sum

        old_y = 0.0
        new_y = old_y - F(old_y) / Fprime(old_y)

        while abs(new_y - old_y) > tolerance:
            old_y = new_y
            new_y = old_y - F(old_y) / Fprime(old_y)

        if compounding == 0:
            return 100 * new_y

        return 100 * compounding * (math.exp(new_y / compounding) - 1)


class absolute_bond(abstract_bond):
    def price(self, curve, date=0):
        pass


class portfolio:
    def __init__(self):
        self.length = 0
        self.bond_array = {}
        self.weights = {}
        self.counter = 1

    def add_bonds(self, bonds, labels=None, allocations=None):
        """
        Adds bonds to a portfolio

        Parameters
        ----------
        bonds: list
            A list of bond objects to be added to the porfolio.
        labels: list
            A list of strings representing labels to assign to the bonds in the first
            argument.  Must either be omitted, or else must be
            a list of the same length as bonds. If omitted, labels will
            be automatically generated. Labels will also be automatically
            generated if any strings in the lest are empty (zero character)
            strings.
        allocations: list
            A list of allocations to assign to the bonds.  Must either
            be omitted or the same length as bonds.  If omitted, an allocation
            of 1 will be assigned to all the bonds.

        Returns
        -------
        None.
        """

        number = len(bonds)

        if labels == None:
            labels = ["" for i in range(number)]

        if len(labels) is not number:
            print("length of bond list and label list must be equal")
            return None

        if allocations is not None and len(allocations) is not number:
            print("length of bond list and allocation list must be equal")
            return None

        for i in range(len(labels)):
            if len(labels[i]) == 0:
                labels[i] = str(self.counter)
                self.counter += 1

        if len(labels) is not len(set(labels)):
            print("duplicate labels: no bonds added")
            return None

        for label in labels:
            if label in self.bond_array:
                print("new label replicates existing label: no bonds added")
                return None

        if allocations is None:
            allocations = [1 for i in range(number)]

        for i in range(number):
            self.bond_array[labels[i]] = bonds[i]
            self.weights[labels[i]] = allocations[i]
        self.length += number

    def print_labels(self):
        """
        Prints out the labels of the contained bonds.

        Parameters
        ----------
        None.

        Returns
        -------
        None.
        """
        for label in self.bond_array:
            print(label)

    def delete_bond(self, label):
        """
        Removes a bond from the portfolio.

        Parameters
        ----------
        label: string
            The label of the bond to be removed.

        Returns
            None.
        """

        if label not in self.bond_array:
            print("label not found: no bond removed")
            return None

        del self.bond_array[label]
        del self.weights[label]
        self.length -= 1

    def __len__(self):
        return self.length

    def price(self, curve, date=0, compounding=0):
        """
        Prices the portfolio with a specified yield curve.

        Parameters
        ----------
        curve: curve
            The first positional argument must be either a
            curve object or a number.  If it is a number,
            it is interpreted as a yield to maturity.
        date: float
            The date on which to price the portfolio (defaults to 0).
        compounding: integer
            The compounding convention if the portfolio is being
            priced with a yield (defaults to continuous
            compounding).
        Returns
        -------
        float
            The calculated portfolio price.
        """

        sum = 0.0
        for key in self.bond_array:
            sum += self.weights[key] * self.bond_array[key].price(
                curve, date, compounding
            )

        return sum

    def dollar(self, curve, date=0, compounding=1):
        """
        Calculates the dollar duration of the portfolio with the inputted
        yield curve.

        Parameters
        ----------
        curve: curve
            The curve object to use to compute the dollar duration.
        date: float
            The date on which to calculate the dollar duration (defaults to 0)
        compounding: integer
            The compounding convention to use to calculate the
            dollar duration (defaults to annual compounding).

        Returns
        -------
        float
            The calculated dollar duration.
        """

        sum = 0.0
        for key in self.bond_array:
            sum += self.weights[key] * self.bond_array[key].dollar(
                curve, date, compounding
            )

        return sum

    def duration(self, curve, date=0, compounding=1):
        """
        Calculates the duration of the portfolio with the inputted yield
        curve.

        Parameters
        ----------
        curve: curve
            The curve object to use to compute the duration.
        date: float
            The date on which to calculate the duration (defaults to 0)
        compounding: integer
            The compounding convention to use to calculate the
            duration (defaults to annual compounding).
        Returns
        -------
        float
            The calculated duration.
        """

        value = self.price(curve, date, compounding)
        w = {}
        for key in self.bond_array:
            w[key] = (
                self.weights[key]
                * self.bond_array[key].price(curve, date, compounding)
                / value
            )

        sum = 0.0
        for key in self.bond_array:
            sum += w[key] * self.bond_array[key].duration(curve, date, compounding)

        return sum

    def convexity(self, curve, date=0, compounding=1):
        """
        Calculates the convexity of the portfolio with the inputted yield
        curve.

        Parameters
        ----------
        curve: curve
            The curve object to use to compute the convexity.
        date: float
            The date on which to calculate the convexity (defaults to 0)
        compounding: integer
            The compounding convention to use to calculate the
            convexity (defaults to annual compounding).

        Returns
        -------
        float
            The calculated convexity.
        """

        value = self.price(curve, date, compounding)
        w = {}
        for key in self.bond_array:
            w[key] = (
                self.weights[key]
                * self.bond_array[key].price(curve, date, compounding)
                / value
            )

        sum = 0.0
        for key in self.bond_array:
            sum += w[key] * self.bond_array[key].convexity(curve, date, compounding)

        return sum


# User functions for constructing yield curves and bonds
def curve_factory(**kwargs):
    """
    Main factory function for constructing curve objects.

    Parameters
    ----------
    Keyword Arguments:
    The arguments must follow one of the following schemes:
        1)
            dates: list
                A list of floats representing the tenors of the benchmark rates.
                The units are assumed to be years.
            rates: list
                A list of floats representing the benchmark interest rates from
                which the yield curve will be constructed by the selected
                interpolation method.  The rates are assumed to be continuously
                compounded and in percentage form.
            compounding: integer
                An integer equal to the compounding frequency of the inputted
                rates.  Must be a positive integer.  If ommitted, the rates are
                treated as continuously compounded
            method: string
                The selected interpolation method:
                    "pwlinear": piecewise linear
                    "hermite": Hermite interpolation (catmull-rom method)
                    "natural": cubic spline with natural boundary conditions.
                Default is piecewise linear.
        2)
            bondlist: list
                A list of bond objects from which the curve will be bootstrapped.
            Note: For this option, the only available interpolation method is
            piecewise linear.
     Returns
    -------
    curve
        The constructed curve object.
    """

    if "dates" in kwargs and "rates" in kwargs:
        if len(kwargs["dates"]) != len(kwargs["rates"]):
            print("Vector of tenors and rates not comensurate")
            return

        rates = []
        if "compounding" in kwargs:
            k = kwargs["compounding"]
            test = int(k)
            if test < 1 or test is not k:
                print("compounding parameter must be a positive integer")
                return

            for rate in kwargs["rates"]:
                cts = k * math.log(1 + rate / 100 / k)
                rates.append(cts)
        else:
            for rate in kwargs["rates"]:
                rates.append(rate / 100)

        if "method" in kwargs:
            method = kwargs["method"]
        else:
            method = "pwlinear"

        if method == "natural" and HASNUMPY == 0:
            print("Natural cubic spline interpolation requires Numpy")
            print("Reverting to piecewise linear interpolation")
            method = "pwlinear"

        yield_curve = curve()
        yield_curve.build_from_rates(kwargs["dates"], rates, method)

        return yield_curve

    if "bondlist" in kwargs:
        if "method" in kwargs and kwargs["method"] is not "pwlinear":
            print(
                "For building curves from bonds, only piecewise linear interpolation is available"
            )
            print("Defaulting to piecewise linear interpolation")

        yield_curve = curve()
        yield_curve.build_from_bonds(kwargs["bondlist"])

        return yield_curve

    print("Invalid inputs")
    return


def bond_factory(dates, rates):
    """
    Main factory function for constructing bond objects.

    Parameters
    ----------
    dates: list
        A list of payment dates for the bond coupons.
    rates: list
        A list of the payments to be made by the bond on the dates specified in
        the dates parameter.

    Returns
    -------
    bond
        The constructed bond object.
    """
    if len(rates) != len(dates):
        print("Coupon vector not commensurate with date vector")
        return

    if all([(type(date) == float) for date in dates]):
        bond = relative_bond(rates, dates)
        return bond

    if all([(type(date) == dt.date) for date in dates]):
        pass

    if all([(type(date) == str) for date in dates]):
        pass

    print("Invalid input list")
    return


def create_flat_curve(rate, compounding=0, max_tenor=100):
    """
    Factory function to construct flat yield curves.

    Parameters
    ----------
    rate: float
        The interest rate level of the flat curve.
    compounding: float
        The compounding convention of the inputted
        rate. Defaults to continuous compounding.
    max_tenor: float or int
        The tenor to use as an argument to the
        curve_factor function.  Defaults to
        100 years.  Not essential, but convenient
        to choose a max_tenor larger than any maturity
        of the bonds that will be priced.

    Returns
    -------
    curve
        The constructed curve object representing a flat
        yield curve.
    """

    if compounding < 0:
        print("invalid compounding convention")
        print("reverting to continuous compounding")

    if compounding > 0:
        rate = compounding * 100 * math.log(1 + rate / compounding / 100)

    return curve_factory(dates=[max_tenor], rates=[rate])


def create_coupon_bond(maturity, face, frequency, rate=0):
    """
    Factory function for constructing coupon bonds.

    Parameters
    ----------
    maturity: float
        The maturity date of the bond.
    face: float
        The face value of the bond.
    rate: float
        The coupon rate of the bond, as a percentage.
    frequency: int
        The annual frequency of coupon payments.

    Returns
    -------
    bond
        The constructed bond object.
    """

    if type(maturity) == str:
        pass

    if frequency < 0:
        print("frequency must be nonnegative")
        return

    if frequency == 0:
        paydates = [float(maturity)]
        payments = [float(face)]

        bond = bond_factory(paydates, payments)
        return bond

    paydates = []
    payments = []

    period = 1.0 / frequency
    date = float(maturity)
    while date > 0:
        paydates.append(date)
        date -= period

    paydates.sort()

    num_of_coupons = len(paydates)
    coupon = (rate / 100.0) * face / frequency

    for i in range(num_of_coupons):
        payments.append(coupon)

    payments[num_of_coupons - 1] += face

    bond = bond_factory(paydates, payments)

    return bond
