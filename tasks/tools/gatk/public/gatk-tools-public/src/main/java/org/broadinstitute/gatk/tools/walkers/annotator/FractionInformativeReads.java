/*
* Copyright 2012-2016 Broad Institute, Inc.
* 
* Permission is hereby granted, free of charge, to any person
* obtaining a copy of this software and associated documentation
* files (the "Software"), to deal in the Software without
* restriction, including without limitation the rights to use,
* copy, modify, merge, publish, distribute, sublicense, and/or sell
* copies of the Software, and to permit persons to whom the
* Software is furnished to do so, subject to the following
* conditions:
* 
* The above copyright notice and this permission notice shall be
* included in all copies or substantial portions of the Software.
* 
* THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
* EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
* OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
* NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
* HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
* WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
* FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
* THE USE OR OTHER DEALINGS IN THE SOFTWARE.
*/

package org.broadinstitute.gatk.tools.walkers.annotator;

import htsjdk.variant.variantcontext.Allele;
import htsjdk.variant.variantcontext.Genotype;
import htsjdk.variant.variantcontext.VariantContext;
import htsjdk.variant.vcf.VCFConstants;
import org.broadinstitute.gatk.tools.walkers.annotator.interfaces.AnnotatorCompatible;
import org.broadinstitute.gatk.tools.walkers.annotator.interfaces.BetaTestingAnnotation;
import org.broadinstitute.gatk.tools.walkers.annotator.interfaces.InfoFieldAnnotation;
import org.broadinstitute.gatk.tools.walkers.annotator.interfaces.ReducibleAnnotation;
import org.broadinstitute.gatk.utils.MathUtils;
import org.broadinstitute.gatk.utils.contexts.AlignmentContext;
import org.broadinstitute.gatk.utils.contexts.ReferenceContext;
import org.broadinstitute.gatk.utils.genotyper.PerReadAlleleLikelihoodMap;
import org.broadinstitute.gatk.utils.refdata.RefMetaDataTracker;
import org.broadinstitute.gatk.utils.variant.GATKVCFConstants;

import java.util.Collections;
import java.util.List;
import java.util.Map;

/**
 * The fraction of reads deemed informative over the entire cohort
 *
 * <p>The FractionInformativeReads annotation produces a single fraction for each site: sum(AD)/sum(DP). The sum in the numerator
 * is over all the samples in the cohort and all the alleles in each sample. The sum in the denominator is over all the samples.
 *
 *
 * <h3>Caveats</h3>
 * <ul>
 *     <li>This annotation can be generated by HaplotypeCaller, MuTect2 or GenotypeGVCFs (it will not work when called from VariantAnnotator).</li>
 * </ul>
 *
 * <h3>Related annotations</h3>
 * <ul>
 *     <li><b><a href="https://www.broadinstitute.org/gatk/guide/tooldocs/org_broadinstitute_gatk_tools_walkers_annotator_DepthPerAlleleBySample.php">DepthPerAlleleBySample</a></b> displays the number of reads supporting each allele, without calculating the fraction.</li>
 * </ul>
 */

public class FractionInformativeReads extends InfoFieldAnnotation implements ReducibleAnnotation, BetaTestingAnnotation {
    @Override
    public String getRawKeyName() {
        return null;
    }

    @Override
    public List<String> getKeyNames() {
        return Collections.singletonList(GATKVCFConstants.FRACTION_INFORMATIVE_READS_KEY);
    }

    @Override
    public Map<String, Object> annotateRawData(RefMetaDataTracker tracker, AnnotatorCompatible walker, ReferenceContext ref, Map<String, AlignmentContext> stratifiedContexts, VariantContext vc, Map<String, PerReadAlleleLikelihoodMap> stratifiedPerReadAlleleLikelihoodMap) {
        return null;
    }

    @Override
    public Map<String, Object> combineRawData(List<Allele> allelesList, List<? extends ReducibleAnnotationData> listOfRawData) {
        return null;
    }

    @Override
    public Map<String, Object> finalizeRawData(VariantContext vc, VariantContext originalVC) {

        int totalAD = 0;
        for (final Genotype gt : vc.getGenotypes()){
            if(gt != null) {
                if(gt.hasAD()) {
                    totalAD += MathUtils.sum(gt.getAD());
                    continue;
                }
                // this is needed since the finalizing of HOM_REF genotypes comes after the finalizing of annotations. so the AD field is null at this point.
                // TODO: this will become unneeded if the above statement is false in which case it can be safely removed.
                if(gt.hasExtendedAttribute(GATKVCFConstants.MIN_DP_FORMAT_KEY)) {
                    totalAD += Integer.parseInt((String) gt.getExtendedAttribute(GATKVCFConstants.MIN_DP_FORMAT_KEY));
                }
            }
        }
        final int depth =  vc.getAttributeAsInt(VCFConstants.DEPTH_KEY, 0);
        return Collections.singletonMap(GATKVCFConstants.FRACTION_INFORMATIVE_READS_KEY, (Object) (depth != 0 ? totalAD / (double) depth : 0));
    }

    @Override
    public void calculateRawData(VariantContext vc, Map<String, PerReadAlleleLikelihoodMap> pralm, ReducibleAnnotationData rawAnnotations) {

    }

    @Override
    public Map<String, Object> annotate(RefMetaDataTracker tracker, AnnotatorCompatible walker, ReferenceContext ref, Map<String, AlignmentContext> stratifiedContexts, VariantContext vc, Map<String, PerReadAlleleLikelihoodMap> stratifiedPerReadAlleleLikelihoodMap) {
        return null;
    }
}
