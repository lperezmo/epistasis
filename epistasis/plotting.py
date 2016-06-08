__doc__ = """ Plotting module setup for matplotlib to plot the results of epistasis models."""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from scipy.stats import norm as scipy_norm
from scipy.stats import f

from seqspace.errors import BaseErrorMap
from seqspace.plotting import PlottingContainer, mpl_missing

# ---------------------------------------------------
# Exceptions
# ---------------------------------------------------

class LogScalingException(Exception):
    """ Exception for handling log scaling problems when plotting. """

# ---------------------------------------------------
# Various plotting classes
# ---------------------------------------------------

class EpistasisPlotting(PlottingContainer):

    def __init__(self, model):
        """ Plots for epistasis models. """
        self.model = model
        super(EpistasisPlotting, self).__init__(self.model)

    def interactions(self, figsize=(6,4), **kwargs):
        fig, ax = bar_with_xbox(self.model, figsize=figsize, **kwargs)
        return fig, ax

class RegressionPlotting(EpistasisPlotting):

    def __init__(self, model):
        """ Reference by model or gpm."""
        self.model = model
        super(RegressionPlotting, self).__init__(self.model)

    def correlation(self, ax=None, figsize=(6,4), **kwargs):
        """ Draw a correlation plot of data. """
        if ax is None:
            fig, ax = plt.subplots(figsize=figsize)
        else:
            fig = ax.get_figure()

        max_p = max(self.model.phenotypes)
        min_p = min(self.model.phenotypes)

        known = self.model.phenotypes
        predicted = self.model.Stats.predict()

        # Add scatter plot points on correlation grid
        ax.plot(known, predicted, 'b.')

        # Add 1:1 correlation line
        ax.plot(np.linspace(min,max, 10), np.linspace(min,max, 10), 'r-')

        ax.set_xlabel("known")
        ax.set_ylabel("learned")

        return fig, ax

    def predicted_phenotypes(self, ax=None, figsize=(6,4), **kwargs):
        """
            Plots the predicted phenotypes
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=figsize)
        else:
            fig = ax.get_figure()

        known = self.model.phenotypes
        predicted = self.model.Stats.predict()

        # Add scatter plot points on correlation grid
        ax.plot(known, 'b-')
        ax.plot(predicted, 'r-')

        ax.set_ylabel("phenotypes")
        ax.set_xlabel("genotypes")

        return fig, ax

    def residuals(self, ax=None, stem=False, figsize=(6,4), axis=None, **kwargs):
        """ Get figure, return figure. """
        if ax is None:
            fig, ax = plt.subplots(figsize=figsize)
        else:
            fig = ax.get_figure()

        theory = self.model.Stats.predict()
        observed = self.model.phenotypes

        # Calculate residuals
        residuals =  theory - observed

        # Build array of residuals next to theoretical value
        # then sort those columns in ascending order of theoretical
        # value for plotting.
        data = np.array((theory, residuals))
        data = data[:, data[0, :].argsort()]

        ylim = max([abs(min(residuals)), abs(max(residuals))])

        # Create a stem plot of the data
        if stem:
            markerline, stemlines, baseline = ax.stem(data[0], data[1], markerfmt=" ", linewidth=6, color='b')
            plt.setp(markerline, 'markerfacecolor', 'b')
            plt.setp(stemlines, 'linewidth', 1.5)
            plt.setp(baseline, 'color','r', 'linewidth', 1)
        else:
            #for i in range(len(data[0])):
             #   print(str(data[0,i]) + "," + str(data[1,i]) + ",")
            ax.plot(data[0], data[1], **kwargs)
            ax.hlines(0, min(data[0]), max(data[0]), linestyle="dotted")
        ax.set_ylim([-ylim, ylim])

        if axis is not None:
            ax.axis(axis)

        return fig, ax

    def best_fit(self, ax=None, figsize=(6,4), errorbars=False, axis=None, **kwargs):
        """ Plot model line through date. """

        # Add to axis if given, else create new plot.
        if ax is None:
            fig, ax = plt.subplots(figsize=figsize)
        else:
            fig = ax.get_figure()

        # Plot line through data
        theory = self.model.Stats.predict()
        observed = self.model.phenotypes

        # Sort the theory for line plot
        sorted_theory = np.sort(theory)

        # Plot the line through data

        if errorbars is True:

                if self.model.log_transform:
                    upper = np.log10(1 + self.model.stdeviations/self.model.Raw.phenotypes)
                    lower = np.log10(1 - self.model.stdeviations/self.model.Raw.phenotypes)

                else:
                    upper = self.stdeviations
                    lower = upper
                ax.errorbar(theory, observed, yerr=[upper,abs(lower)], **kwargs)
        else:
            ax.plot(theory, observed, **kwargs)
        ax.plot(sorted_theory, sorted_theory, color="r", linewidth=2)

        if axis is not None:
            ax.axis(axis)

        return fig, ax

    def summary(self, ):
        """ Plot a summary of the model. Includes a plot of
            the model with residuals plotted underneath.
        """
        pass


class NonlinearPlotting(RegressionPlotting):

    def __init__(self, model):
        """ Reference by model or gpm."""
        self.model = model
        super(NonlinearPlotting, self).__init__(self.model)

    def linear_phenotypes(self):
        """ P vs. p plot. """
        fig, ax = plt.subplots()

        known = self.model.phenotypes
        predicted = np.dot(self.model.X,  self.model.Interactions.values)


        # Add scatter plot points on correlation grid
        ax.plot(predicted, known, 'b.')

        ax.set_xlabel("linear phenotypes")
        ax.set_ylabel("nonlinear phenotypes")

        return fig, ax

    def nonlinear_function(self, ax=None, xbounds=None, figsize=(6,4), **kwargs):
        """ Plot the input function for set of phenotypes. """
        if ax is None:
            fig, ax = plt.subplots(figsize=figsize)
        else:
            fig = ax.get_figure()

        params = self.model.Parameters._param_list

        # Get the values
        values = [getattr(self.model.Parameters, p) for p in params]

        if xbounds is None:
            predicted = np.dot(self.model.X,  self.model.Interactions.values)

            if self.model.Linear.log_transform:
                predicted = 10**predicted

            max_p = max(predicted)
            min_p = min(predicted)

        else:
            max_p = xbounds[1]
            min_p = xbounds[0]

        x = np.linspace(min_p, max_p, 1000)
        y = self.model.function(x, *values)
        ax.plot(x,y, **kwargs)

        return fig, ax


    def best_fit(self, ax=None, figsize=(6,4), errorbars=False, axis=None, **kwargs):
        """ Plot model line through data.

        Parameters:
        ----------
        ax : matplotlib.Axis
            matplotlib object to add best fit data to.

        """
        # Add to axis if given, else create new plot.
        if ax is None:
            fig, ax = plt.subplots(figsize=figsize)
        else:
            fig = ax.get_figure()

        # Plot line through data
        linear = self.model.Stats.linear()
        theory = self.model.Stats.predict()
        observed = self.model.phenotypes

        data = np.array((linear, theory))
        data = data[:, data[0, :].argsort()]

        # Plot the line through data

        if errorbars is True:
                if self.model.Linear.log_transform:
                    upper = np.log10(1 + self.model.stdeviations/self.model.phenotypes)
                    lower = np.log10(1 - self.model.stdeviations/self.model.phenotypes)

                else:
                    upper = self.model.stdeviations
                    lower = upper

                ax.errorbar(linear, observed, yerr=[upper,abs(lower)], **kwargs)
        else:
            ax.plot(linear, observed, '.', **kwargs)

        #ax.plot(data[0], data[1], color="r", linewidth=2)
        fig, ax = self.nonlinear_function(ax=ax, color="r", linewidth=2)

        if axis is not None:
            ax.axis(axis)

        return fig, ax

    def residuals(self, ax=None, figsize=(6,4), stem=False, axis=None, **kwargs):
        """ Get figure, return figure. """

        if ax is None:
            fig, ax = plt.subplots(figsize=figsize)
        else:
            fig = ax.get_figure()


        theory = self.model.Stats.predict()
        linear = self.model.Stats.linear()
        observed = self.model.phenotypes

        # Calculate residuals
        residuals =  theory - observed

        # Build array of residuals next to theoretical value
        # then sort those columns in ascending order of theoretical
        # value for plotting.
        data = np.array((linear, residuals))
        data = data[:, data[0, :].argsort()]

        ylim = max([abs(min(residuals)), abs(max(residuals))])

        # Create a stem plot of the data
        if stem:
            markerline, stemlines, baseline = ax.stem(data[0], data[1], markerfmt=" ", linewidth=6, color='b')
            plt.setp(markerline, 'markerfacecolor', 'b')
            plt.setp(stemlines, 'linewidth', 1.5)
            plt.setp(baseline, 'color','r', 'linewidth', 1)
        else:
            ax.errorbar(data[0], data[1], **kwargs)
            ax.hlines(0, min(data[0]), max(data[0]), linestyle="dotted")
        ax.set_ylim([-ylim, ylim])

        # Set axis if given
        if axis is not None:
            ax.axis(axis)

        return fig, ax

class SpecifierPlotting(PlottingContainer):

    def __init__(self, specifier):
        """ Specifier Plotting object. """
        self.specifier

class FDistributionPlotting(object):

    @mpl_missing # Don't use this plotting object in outside classes if mpl is not installed
    def __init__(self, FDistribution):
        """Plotting a distribution. """
        self._dist = FDistribution

    def pdf(self, percent_start=0.0001, percent_end=0.9999, figsize=(6,4), **kwargs):
        """ Plot the distribution. """
        #Build distribution
        x = np.linspace(self._dist.ppf(percent_start),
                        self._dist.ppf(percent_end), 1000)

        y = self._dist.pdf(x)

        # Plot
        fig, ax = plt.subplots(figsize=figsize)
        ax.plot(x, y, **kwargs)
        ax.set_title("Probability density function")
        ax.set_xlabel("F-statistic")
        ax.set_ylabel("Probability density")
        return fig, ax

    def cdf(self, percent_start=0.0001, percent_end=0.9999, figsize=(6,4), **kwargs):
        #Build distribution
        x = np.linspace(self._dist.ppf(percent_start),
                        self._dist.ppf(percent_end), 1000)

        y = self._dist.cdf(x)

        # Plot
        fig, ax = plt.subplots(figsize=figsize)
        ax.plot(x, y, **kwargs)
        ax.set_title("Cumulative distribution function")
        ax.set_xlabel("F-statistic")
        ax.set_ylabel("Cumulative probability")

        return fig, ax

# ---------------------------------------------------
# Epistasis Graphing
# ---------------------------------------------------


def magnitude_vs_order(model, keep_sign=False,
        marker="o",
        color="b",
        linestyle="None",
        xlabel="Order",
        ylabel="Magnitude",
        title="",
        figsize=(6,4),
        errorbars=True,
        **kwargs):
    """
        Generate a plot of magnitude versus order.

    """
    orders = range(1, model.length+1)
    magnitudes = []
    errors = []
    for i in orders:
        coeffs = np.array(list(model.Interactions.get_order(i).values()))

        # Do we care about signs?
        if keep_sign is False:
            coeffs = abs(coeffs)

        # Add magnitudes
        magnitudes.append(np.mean(coeffs))
        errors.append(np.std(coeffs))

    # Initialize the figure and axis
    fig, ax = plt.subplots(figsize=figsize)

    # Create plot
    if errorbars:
        ax.errorbar(orders, magnitudes, yerr=errors, marker=marker, color=color, linestyle=linestyle, **kwargs)

    else:
        ax.plot(orders, magnitudes, marker=marker, color=color, linestyle=linestyle, **kwargs)

    # Steal the max bound, cause matplotlib does a great job of picking good axis
    ylimits = max(list(ax.get_ylim()))
    # Make y limits symmetric
    ax.axis([orders[0], orders[-1], -ylimits, ylimits])




    # Add a line at zero if keeping sign
    if keep_sign:
        ax.hlines(0, orders[0], orders[-1], linestyle="--")

    return fig, ax


def bar_with_xbox(model,
    order_colors=("red","orange","green","purple","DeepSkyBlue","yellow","pink"),
    significance="bon",
    significance_cutoff=0.05,
    sigmas=1,
    log_space=False,
    y_scalar=1.5,
    y_axis_name="interaction",
    figsize=(8,10),
    height_ratio=12,
    star_cutoffs=(0.05,0.01,0.001),
    star_spacer=0.0075,
    ybounds=None,
    bar_borders=True,
    capsize=2,
    xgrid=True):
    """
    Create a barplot with the values from model, drawing the x-axis as a grid of
    boxes indicating the coordinate of the epistatic parameter. Should automatically
    generate an almost publication-quality figure.

    input:
        model: epistasis model
        order_colors: list/tuple of colors for each order (rgb,html string-like)
        significance: how to treat signifiance.  should be:
                      "bon" -> Bonferroni corrected p-values (default)
                      "p" -> raw p-values
                      None -> ignore significance
        significance_cutoff: value above which to consider a term significant
        sigmas: number of sigmas to show for each error bar
        y_scalar: how much to scale the y-axis above and beyond y-max
        y_axis_name: what to put on the y-axis of the barplot

        figsize: tuple of figure width,height
        height_ratio: how much to scale barplot relative to xbox
        star_cutoffs: signifiance cutoffs for star stack.  should go from highest
                      p to lowest p (least to most significant)
        star_spacer: constant that scales how closely stacked stars are from one
                     another

    output:
        pretty-graph objects fig and ax_array (ax_array has two entries for top
        and bottom panels)
    """
    # Sanity check on the errors
    if sigmas == 0:
        significance = None
    elif significance == None:
        sigmas = 0

    # Grab the fit values and labels, tossing 0th-order term

    labels = model.Interactions.labels[1:]

    # Figure out the length of the x-axis and the highest epistasis observed
    num_terms = len(labels)
    highest_order = max([len(l) for l in labels])

    # Figure out how many sites are in the dataset (in case of non-binary system)
    all_sites = []
    for l in labels:
        all_sites.extend(l)
    all_sites = list(dict([(s,[]) for s in all_sites]).keys())
    all_sites.sort()
    num_sites = len(all_sites)

    # Figure out how to color each order
    if order_colors == None:
        order_colors = ["gray" for i in range(highest_order+1)]
    else:
        if len(order_colors) < highest_order:
            err = "order_colors has too few entries (at least {:d} needed)\n".format(highest_order)
            raise ValueError(err)

        # Stick gray in the 0 position for insignificant values
        order_colors = list(order_colors)
        order_colors.insert(0,"gray")

    # ---------------------- #
    # Deal with significance #
    # ---------------------- #

    # NEED TO RETURN TO SIGNIFICANCE FUNCTIONS

    if sigmas == 0:

        significance = None

    else:

        # If log transformed, need to get raw values for normal distribution
        if model.log_transform:

            beta = model.Interactions.Raw.values[1:]
            sigma_beta = model.Interactions.Raw.err.upper[1:]
            z_score =  abs( (beta  - 1 )/sigma_beta )

        # else, just grab standard values
        else:
            beta = model.Interactions.values[1:]
            sigma_beta = model.Interactions.err.upper[1:]
            z_score =  abs( (beta)/sigma_beta )

        # if z_score is > 5, set z_score to largest possible range where p-value is within floating point
        z_score[z_score > 8.2] = 8.2

    # straight p-values
    if significance == "p":
        p_values = 2*(1 - scipy_norm.cdf( z_score ) )

    # bonferroni corrected p-values
    elif significance == "bon":
        p_values = 2*(1 - scipy_norm.cdf( z_score ) ) * len(beta)

    # ignore p-values and color everything
    elif significance == None:
        p_values = [0 for i in range(len(labels))]
        significance_cutoff = 1.0

    # or die
    else:
        err = "signifiance argument {:s} not recognized\n".format(significance)
        raise ValueError(err)

    # Create color array based on significance
    color_array = np.zeros((len(labels)),dtype=int)
    for i, l in enumerate(labels):
        if p_values[i] < significance_cutoff:
            color_array[i] = len(l) - 1
        else:
            color_array[i] = -1

    # ---------------- #
    # Create the plots #
    # ---------------- #

    # Make a color map
    cmap = mpl.colors.ListedColormap(colors=order_colors)
    cmap.set_bad(color='w', alpha=0) # set the 'bad' values (nan) to be white and transparent
    bounds = range(-1,len(order_colors))
    norm = mpl.colors.BoundaryNorm(bounds, cmap.N)

    if xgrid is True:
        fig = plt.figure(figsize=figsize)

        # Create a plot with an upper and lower panel, sharing the x-axis
        gs = mpl.gridspec.GridSpec(2, 1, height_ratios=[height_ratio, 1])
        ax = [plt.subplot(gs[0])]
        ax.append(plt.subplot(gs[1],sharex=ax[0]))
        bar_axis = ax[0]
        grid_axis = ax[1]


        ###### Create the box-array x-axis

        # make an empty data set
        data = np.ones((num_sites,num_terms),dtype=int)*np.nan

        # Make entries corresponding to each coordinate 1
        for i, l in enumerate(labels):
            for j in l:
                data[(j-1),i] = color_array[i]

        # draw the grid
        for i in range(num_terms + 1):
            grid_axis.add_artist(mpl.lines.Line2D((i,i),
                                                           (0,num_sites),
                                                           color="black"))

        for i in range(num_sites + 1):
            grid_axis.add_artist(mpl.lines.Line2D((0,num_terms),
                                                           (i,i),
                                                           color="black"))

        # draw the boxes
        grid_axis.imshow(data, interpolation='nearest',cmap=cmap,norm=norm,
                           extent=[0, num_terms, 0, num_sites], zorder=0)

        # turn off the axis labels
        grid_axis.set_frame_on(False)
        grid_axis.axis("off")
        grid_axis.set_xticklabels([])
        grid_axis.set_yticklabels([])

    else:

        fig, ax = plt.subplots(figsize=figsize)
        bar_axis = ax


    # ------------------ #
    # Create the barplot #
    # ------------------ #

    # set up bar colors
    colors_for_bar = np.array([mpl.colors.colorConverter.to_rgba(order_colors[(i+1)]) for i in color_array])

    # Plot error if sigmas are given.
    if sigmas == 0:

        if log_space:
            # Make sure the space is log-transformed
            if model.log_transform is False:
                raise LogScalingException(""" A log scale cannot be used, because the genotype-phenotype map was never log-transformed.""")


            else:
                bar_y = model.Interactions.values[1:]

        else:
            if model.log_transform:
                bar_y = model.Interactions.Raw.values[1:]
            else:
                bar_y = model.Interactions.values[1:]

        bar_axis.bar(range(len(bar_y)), bar_y, width=0.8, color=colors_for_bar, edgecolor="none")

    else:

        # Plot the graph on a log scale
        if log_space:

            try:
                upper = BaseErrorMap.transform_upper(sigmas*model.Interactions.Raw.err.upper, model.Interactions.Raw.values, logbase=model.logbase)
                lower = BaseErrorMap.transform_lower(sigmas*model.Interactions.Raw.err.lower, model.Interactions.Raw.values, logbase=model.logbase)
                bar_y = model.Interactions.values[1:]

            except AttributeError:
                raise LogScalingException(""" A log scale cannot be used, because the genotype-phenotype map was never log-transformed.""")

        # else if the space is log transformed, plot the non-log interaction values
        elif model.log_transform:

            upper = sigmas * model.Interactions.Raw.err.upper
            lower = sigmas * model.Interactions.Raw.err.lower
            bar_y = model.Interactions.Raw.values[1:]

        # Else plot the interaction values
        else:
            upper = sigmas * model.Interactions.err.upper
            lower = sigmas * model.Interactions.err.lower
            bar_y = model.Interactions.values[1:]

        yerr = [lower[1:], upper[1:]]
        bar_axis.bar(range(len(bar_y)), bar_y, width=0.8, yerr=yerr, color=colors_for_bar,
                        error_kw={"ecolor":"black", "capsize":capsize},
                        edgecolor="none",
                        linewidth=2,
                        )

    bar_axis.hlines(0, 0, len(model.Interactions.values)-1, linewidth=1, linestyle="--")

    # Label barplot y-axis
    bar_axis.set_ylabel(y_axis_name, fontsize=14)

    # Set barplot y-scale
    if ybounds is None:
        ymin = -y_scalar*max(abs(bar_y))
        ymax =  y_scalar*max(abs(bar_y))
    else:
        ymin = ybounds[0]
        ymax = ybounds[1]

    # Make axes pretty pretty
    bar_axis.axis([-1, len(bar_y) + 1, ymin, ymax])
    bar_axis.set_frame_on(False) #axis("off")
    bar_axis.get_xaxis().set_visible(False)
    bar_axis.get_yaxis().tick_left()
    bar_axis.get_yaxis().set_tick_params(direction='out')
    bar_axis.add_artist(mpl.lines.Line2D((-1,-1), (bar_axis.get_yticks()[1], bar_axis.get_yticks()[-2]), color='black', linewidth=1))

    # add vertical lines between order breaks
    previous_order = 1
    for i in range(len(labels)):
        if len(labels[i]) != previous_order:
            bar_axis.add_artist(mpl.lines.Line2D((i,i),
               (ymin,ymax),
               color="black",
               linestyle="--"))
            previous_order = len(labels[i])

    # ------------------------- #
    # Create significance stars #
    # ------------------------- #
    if sigmas != 0:
        min_offset = star_spacer*(ymax-ymin)
        for i in range(len(p_values)):

            star_counter = 0
            for j in range(len(star_cutoffs)):
                if p_values[i] < star_cutoffs[j]:
                    star_counter += 1
                else:
                    break

            for j in range(star_counter):
                bar_axis.text(x=(i+0.5),y=ymin+(j*min_offset),s="*")

    # remove x tick labels
    plt.setp([a.get_xticklabels() for a in fig.axes[:-1]], visible=False)

    # Draw the final figure
    fig.tight_layout()

    return fig, ax


def interactions(beta,
    labels,
    err=None,
    order_colors=("red","orange","green","purple","DeepSkyBlue","yellow","pink"),
    significance="bon",
    significance_cutoff=0.05,
    sigmas=1,
    log_space=False,
    y_scalar=1.5,
    y_axis_name="interaction",
    figsize=(8,10),
    height_ratio=12,
    star_cutoffs=(0.05,0.01,0.001),
    star_spacer=0.0075,
    ybounds=None,
    bar_borders=True,
    capsize=2,
    xgrid=True,
    colorall=False):
    """
    Create a barplot with the values from model, drawing the x-axis as a grid of
    boxes indicating the coordinate of the epistatic parameter. Should automatically
    generate an almost publication-quality figure.

    input:
        model: epistasis model
        order_colors: list/tuple of colors for each order (rgb,html string-like)
        significance: how to treat signifiance.  should be:
                      "bon" -> Bonferroni corrected p-values (default)
                      "p" -> raw p-values
                      None -> ignore significance
        significance_cutoff: value above which to consider a term significant
        sigmas: number of sigmas to show for each error bar
        y_scalar: how much to scale the y-axis above and beyond y-max
        y_axis_name: what to put on the y-axis of the barplot

        figsize: tuple of figure width,height
        height_ratio: how much to scale barplot relative to xbox
        star_cutoffs: signifiance cutoffs for star stack.  should go from highest
                      p to lowest p (least to most significant)
        star_spacer: constant that scales how closely stacked stars are from one
                     another

    output:
        pretty-graph objects fig and ax_array (ax_array has two entries for top
        and bottom panels)
    """
    if labels[0] == [0] :
        labels = labels[1:]
        beta = beta[1:]

    # Sanity check on the errors
    if sigmas == 0:
        significance = None
    elif significance == None:
        sigmas = 0

    # If two errorbars are given, assume assymmetry.
    if len(err) == 2:
        lower = err[0][1:]
        upper = err[1][1:]
    else:
        lower = err[1:]
        upper = err[1:]

    # Figure out the length of the x-axis and the highest epistasis observed
    num_terms = len(labels)
    highest_order = max([len(l) for l in labels])

    # Figure out how many sites are in the dataset (in case of non-binary system)
    all_sites = []
    for l in labels:
        all_sites.extend(l)
    all_sites = list(dict([(s,[]) for s in all_sites]).keys())
    all_sites.sort()
    num_sites = len(all_sites)

    # Figure out how to color each order
    if order_colors == None:
        order_colors = ["gray" for i in range(highest_order+1)]
    else:
        if len(order_colors) < highest_order:
            err = "order_colors has too few entries (at least {:d} needed)\n".format(highest_order)
            raise ValueError(err)

        # Stick gray in the 0 position for insignificant values
        order_colors = list(order_colors)
        order_colors.insert(0,"gray")

    # ---------------------- #
    # Deal with significance #
    # ---------------------- #

    # NEED TO RETURN TO SIGNIFICANCE FUNCTIONS

    if sigmas == 0:
        significance = None
    else:
        if log_space == True:
            error_array = np.empty(len(beta), dtype=float)

            # Find indices of negative betas
            negative = np.arange(len(beta), dtype=int)[beta<1]
            positive = np.arange(len(beta), dtype=int)[beta>1]

            error_array[negative] = upper[negative]
            error_array[positive] = lower[positive]
            z_score = abs( (beta - 1) / error_array )

        else:
            z_score = abs( (beta - 1) / err )
        # if z_score is > 5, set z_score to largest possible range where p-value is within floating point
        z_score[z_score > 8.2] = 8.2

    # straight p-values
    if significance == "p":
        p_values = 2*(1 - scipy_norm.cdf( z_score ) )
        print(p_values[-1])

    # bonferroni corrected p-values
    elif significance == "bon":
        p_values = 2*(1 - scipy_norm.cdf( z_score ) ) * len(beta)

    # ignore p-values and color everything
    elif significance == None:
        p_values = [0 for i in range( len(labels) )]
        significance_cutoff = 1.0

    # or die
    else:
        err = "significance argument {:s} not recognized\n".format(significance)
        raise ValueError(err)

    # Create color array based on significance
    color_array = np.zeros((len(labels)),dtype=int)
    for i, l in enumerate(labels):
        if colorall == True:
            color_array[i] = len(l) - 1
        else:
            if p_values[i] < significance_cutoff:
                color_array[i] = len(l) - 1
            else:
                color_array[i] = -1

    # ---------------- #
    # Create the plots #
    # ---------------- #

    # Make a color map
    cmap = mpl.colors.ListedColormap(colors=order_colors)
    cmap.set_bad(color='w', alpha=0) # set the 'bad' values (nan) to be white and transparent
    bounds = range(-1,len(order_colors))
    norm = mpl.colors.BoundaryNorm(bounds, cmap.N)

    if xgrid is True:
        fig = plt.figure(figsize=figsize)

        # Create a plot with an upper and lower panel, sharing the x-axis
        gs = mpl.gridspec.GridSpec(2, 1, height_ratios=[height_ratio, 1])
        ax = [plt.subplot(gs[0])]
        ax.append(plt.subplot(gs[1],sharex=ax[0]))
        bar_axis = ax[0]
        grid_axis = ax[1]


        ###### Create the box-array x-axis

        # make an empty data set
        data = np.ones((num_sites,num_terms),dtype=int)*np.nan

        # Make entries corresponding to each coordinate 1
        for i, l in enumerate(labels):
            for j in l:
                data[(j-1),i] = color_array[i]

        # draw the grid
        for i in range(num_terms + 1):
            grid_axis.add_artist(mpl.lines.Line2D((i,i),
                                                           (0,num_sites),
                                                           color="black"))

        for i in range(num_sites + 1):
            grid_axis.add_artist(mpl.lines.Line2D((0,num_terms),
                                                           (i,i),
                                                           color="black"))

        # draw the boxes
        grid_axis.imshow(data, interpolation='nearest',cmap=cmap,norm=norm,
                           extent=[0, num_terms, 0, num_sites], zorder=0)

        # turn off the axis labels
        grid_axis.set_frame_on(False)
        grid_axis.axis("off")
        grid_axis.set_xticklabels([])
        grid_axis.set_yticklabels([])

    else:

        fig, ax = plt.subplots(figsize=figsize)
        bar_axis = ax


    # ------------------ #
    # Create the barplot #
    # ------------------ #

    # set up bar colors
    colors_for_bar = np.array([mpl.colors.colorConverter.to_rgba(order_colors[(i+1)]) for i in color_array])

    # Plot error if sigmas are given.
    if sigmas == 0:
        if log_space:
            bar_y = np.log10(beta)
        else:
            bar_y = beta

        bar_axis.bar(range(len(bar_y)), bar_y, width=0.8, color=colors_for_bar, edgecolor="none")

    else:

        # Plot the graph on a log scale
        if log_space:
            upper = sigmas*np.log10(1 + upper/beta)
            lower = sigmas*abs(np.log10(1 - lower/beta))
            lower = np.nan_to_num(lower)
            lower[lower == 0] = 10e100

            bar_y = np.log10(beta)
        else:
            upper = sigmas*upper
            lower = sigmas*lower
            bar_y = beta


        lower[lower > y_scalar*max(abs(bar_y))] = max(abs(bar_y)) + y_scalar*max(abs(bar_y))
        upper[upper > y_scalar*max(abs(bar_y))] =  max(abs(bar_y)) + y_scalar*max(abs(bar_y))

        yerr = [lower, upper]

        bar_axis.bar(range(len(bar_y)), bar_y, width=0.8, yerr=yerr, color=colors_for_bar,
                        error_kw={"ecolor":"black", "capsize":capsize},
                        edgecolor="none",
                        linewidth=2,
        )

    bar_axis.hlines(0, 0, len(beta)-1, linewidth=1, linestyle="--")

    # Label barplot y-axis
    bar_axis.set_ylabel(y_axis_name, fontsize=14)

    # Set barplot y-scale
    if ybounds is None:
        ymin = -y_scalar*max(abs(bar_y))
        ymax =  y_scalar*max(abs(bar_y))
    else:
        ymin = ybounds[0]
        ymax = ybounds[1]

    # Make axes pretty pretty
    bar_axis.axis([-1, len(bar_y) + 1, ymin, ymax])
    bar_axis.set_frame_on(False) #axis("off")
    bar_axis.get_xaxis().set_visible(False)
    bar_axis.get_yaxis().tick_left()
    bar_axis.get_yaxis().set_tick_params(direction='out')
    bar_axis.add_artist(mpl.lines.Line2D((-1,-1), (bar_axis.get_yticks()[1], bar_axis.get_yticks()[-2]), color='black', linewidth=1))

    # add vertical lines between order breaks
    previous_order = 1
    for i in range(len(labels)):
        if len(labels[i]) != previous_order:
            bar_axis.add_artist(mpl.lines.Line2D((i,i),
               (ymin,ymax),
               color="black",
               linestyle="--"))
            previous_order = len(labels[i])

    # ------------------------- #
    # Create significance stars #
    # ------------------------- #
    if sigmas != 0:
        min_offset = star_spacer*(ymax-ymin)
        for i in range(len(p_values)):

            star_counter = 0
            for j in range(len(star_cutoffs)):
                if p_values[i] < star_cutoffs[j]:
                    star_counter += 1
                else:
                    break

            for j in range(star_counter):
                bar_axis.text(x=(i+0.5),y=ymin+(j*min_offset),s="*")

    # remove x tick labels
    plt.setp([a.get_xticklabels() for a in fig.axes[:-1]], visible=False)

    # Draw the final figure
    fig.tight_layout()

    return fig, ax












# -----------------------------
# Plotting PCA
# -----------------------------

def principal_components(model, with_components=True, dimensions=3, figsize=[6,6], ac="r"):
    """
        Arguments:
        ---------
        model: EpistasisPCA object
            PCA model of epistasis to plot
        figsize: array like
            Figure size
        ac: str
            Color for arrows representing principal components

    """
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111, projection="3d")

    if dimensions > 3:
        raise Exception(""" Cannot plot greater than 3 dimensions! """)

    # Plot the principal components?
    if with_components:

        x,y,z  = 0,0,0

        U1 = model.components[0][0] * 0.03
        V1 = model.components[0][1] * 0.03
        W1 = model.components[0][2] * 0.03
        U2 = model.components[1][0] * 0.03
        V2 = model.components[1][1] * 0.03
        W2 = model.components[1][2] * 0.03
        U3 = model.components[2][0] * 0.03
        V3 = model.components[2][1] * 0.03
        W3 = model.components[2][2] * 0.03

        # PCA
        a = Arrow3D([-U1,U1], [-V1,V1], [-W1,W1], mutation_scale=20, lw=2, arrowstyle="->", color="r")
        b = Arrow3D([-U2,U2], [-V2,V2], [-W2,W2], mutation_scale=20, lw=2, arrowstyle="->", color="r")
        c = Arrow3D([-U3,U3], [-V3,V3], [-W3,W3], mutation_scale=20, lw=2, arrowstyle="->", color="r")

        ax.add_artist(a)
        ax.add_artist(b)
        ax.add_artist(c)

    # Print transformed phenotypes?
    for i in model.X_new:
        ax.scatter(i[0],i[1],i[2], s=100)

    mapping = model.get_map("indices", "X_new")
    model.Graph.build_graph()

    for edge in model.Graph.edges():
        ax.plot((mapping[edge[0]][0], mapping[edge[1]][0]),
                (mapping[edge[0]][1], mapping[edge[1]][1]),
                (mapping[edge[0]][2], mapping[edge[1]][2]),
                linewidth=2,
               c='grey')

    @interact
    def angle(angle=(0,360,10), elevation=(-100,100,10)):
        ax.view_init(azim=angle, elev=elevation)
        return fig


# -----------------------------
# Useful plots for analyzing data
# from regression data.
# -----------------------------

def correlation(learned, known, title="Known vs. Learned", figsize=[6,6]):
    """ Create a plot showing the learned data vs. known data. """

    fig, ax = plt.subplots(1,1, dpi=300, figsize=figsize)

    ax.plot(known, learned, '.b')
    ax.hold(True)
    x = np.linspace(min(known), max(known), 1000)
    ax.plot(x,x, '-r', linewidth=1)
    ax.set_xlabel("Known", fontsize = 14)
    ax.set_ylabel("Learned", fontsize=14)
    ax.set_title(title, fontsize=14)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.yaxis.set_ticks_position('left')
    ax.xaxis.set_ticks_position('bottom')

    return fig

def residuals(learned, known, title="Residual Plot", figsize=[6,4]):
    """ Generate a residual plot. """
    fig, ax = plt.subplots(1,1, dpi=300, figsize=figsize)

    ax.stem(known, (learned-known), 'b-', markerfmt='.')
    ax.set_title(title, fontsize=20)
    ax.set_xlabel("True")
    ax.set_ylabel("Residuals")

    return fig
